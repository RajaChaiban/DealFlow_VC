"""
Orchestrator Agent for DealFlow AI Copilot.

Master coordinator that manages the entire analysis pipeline:
- Runs extraction first (sequential, as it's the foundation)
- Triggers analysis, risk, and valuation agents in parallel
- Handles status updates and progress tracking
- Implements error recovery and retry logic
- Synthesizes all outputs into cohesive IC memo

Target: Complete full analysis in 30-60 seconds.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Optional

from PIL import Image

from app.agents.analysis_agent import AnalysisAgent
from app.agents.base import AgentContext, BaseAgent
from app.agents.extraction_agent import ExtractionAgent
from app.agents.risk_agent import RiskAgent
from app.agents.valuation_agent import ValuationAgent
from app.core.gemini_client import GeminiClient, get_gemini_client
from app.models.schemas import (
    AgentExecutionStatus,
    AgentStatus,
    AnalysisResult,
    ConfidenceLevel,
    ExecutiveSummary,
    ExtractionResult,
    ICMemo,
    OrchestratorProgress,
    RecommendationType,
    RiskResult,
    ValuationResult,
)
from app.utils.exceptions import AnalysisError
from app.utils.logger import logger


class OrchestratorAgent:
    """
    Master orchestrator that coordinates all agents for deal analysis.

    Execution flow:
    1. SEQUENTIAL: Extraction Agent (foundational data)
    2. PARALLEL: Analysis, Risk, and Valuation Agents
    3. SYNTHESIS: Combine all outputs into IC Memo

    Features:
    - Progress tracking and status updates
    - Error recovery with retries
    - Timeout handling
    - Result caching via context

    Example:
        ```python
        orchestrator = OrchestratorAgent()

        # Register progress callback
        orchestrator.on_progress(lambda p: print(f"{p.progress_percentage}% complete"))

        # Run analysis
        result = await orchestrator.analyze(
            images=pdf_images,
            text_content=extracted_text
        )
        print(result.final_recommendation)
        ```
    """

    def __init__(
        self,
        gemini_client: Optional[GeminiClient] = None,
        max_parallel_agents: int = 3,
        timeout_seconds: int = 300,  # 5 minute max
    ) -> None:
        """
        Initialize the orchestrator.

        Args:
            gemini_client: Shared Gemini client for all agents
            max_parallel_agents: Maximum concurrent agent executions
            timeout_seconds: Overall timeout for full analysis
        """
        self.client = gemini_client or get_gemini_client()
        self.max_parallel_agents = max_parallel_agents
        self.timeout_seconds = timeout_seconds

        # Agent instances
        self.extraction_agent = ExtractionAgent(gemini_client=self.client)
        self.analysis_agent = AnalysisAgent(gemini_client=self.client)
        self.risk_agent = RiskAgent(gemini_client=self.client)
        self.valuation_agent = ValuationAgent(gemini_client=self.client)

        # Execution state
        self.context = AgentContext()
        self._progress_callbacks: list[Callable[[OrchestratorProgress], None]] = []
        self._current_progress: Optional[OrchestratorProgress] = None
        self._started_at: Optional[datetime] = None

    def on_progress(
        self,
        callback: Callable[[OrchestratorProgress], None],
    ) -> None:
        """
        Register a progress callback.

        Args:
            callback: Function called with progress updates
        """
        self._progress_callbacks.append(callback)

    def _emit_progress(self, progress: OrchestratorProgress) -> None:
        """Emit progress to all registered callbacks."""
        self._current_progress = progress
        for callback in self._progress_callbacks:
            try:
                callback(progress)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")

    async def analyze(
        self,
        images: Optional[list[Image.Image]] = None,
        text_content: Optional[str] = None,
        company_name_hint: Optional[str] = None,
        fast_mode: bool = False,
    ) -> ICMemo:
        """
        Run full deal analysis pipeline.

        Args:
            images: PDF pages as PIL Images
            text_content: Extracted text from PDF
            company_name_hint: Optional company name hint
            fast_mode: Skip some analyses for speed

        Returns:
            Complete IC Memo with all analysis results

        Raises:
            AnalysisError: If critical errors occur
        """
        self._started_at = datetime.utcnow()
        self.context.clear()

        logger.info("=" * 60)
        logger.info("ORCHESTRATOR: Starting Deal Analysis Pipeline")
        logger.info("=" * 60)

        try:
            # Execute with overall timeout
            result = await asyncio.wait_for(
                self._execute_pipeline(
                    images=images,
                    text_content=text_content,
                    company_name_hint=company_name_hint,
                    fast_mode=fast_mode,
                ),
                timeout=self.timeout_seconds,
            )

            total_time = (datetime.utcnow() - self._started_at).total_seconds()
            logger.info("=" * 60)
            logger.info(f"ORCHESTRATOR: Pipeline Complete in {total_time:.1f}s")
            logger.info("=" * 60)

            return result

        except asyncio.TimeoutError:
            logger.error(
                f"ORCHESTRATOR: Pipeline timed out after {self.timeout_seconds}s"
            )
            raise AnalysisError(
                message=f"Analysis pipeline timed out after {self.timeout_seconds}s",
                error_code="ORCHESTRATOR_TIMEOUT",
            )

    async def _execute_pipeline(
        self,
        images: Optional[list[Image.Image]],
        text_content: Optional[str],
        company_name_hint: Optional[str],
        fast_mode: bool,
    ) -> ICMemo:
        """Execute the full analysis pipeline."""
        # Phase 1: Extraction (Sequential - Foundation)
        self._update_progress(
            phase="extraction",
            percentage=5,
            message="Starting data extraction from pitch deck...",
        )

        extraction_result = await self._run_extraction(
            images=images,
            text_content=text_content,
            company_name_hint=company_name_hint,
        )
        self.context.set("extraction", extraction_result)

        self._update_progress(
            phase="extraction",
            percentage=30,
            message=f"Extracted data for {extraction_result.company_name}",
        )

        # Phase 2: Parallel Analysis
        self._update_progress(
            phase="parallel_analysis",
            percentage=35,
            message="Running parallel analysis agents...",
        )

        analysis_result, risk_result, valuation_result = await self._run_parallel_analysis(
            extraction_result=extraction_result,
            fast_mode=fast_mode,
        )

        self.context.set("analysis", analysis_result)
        self.context.set("risk", risk_result)
        self.context.set("valuation", valuation_result)

        self._update_progress(
            phase="synthesis",
            percentage=85,
            message="Synthesizing results into IC memo...",
        )

        # Phase 3: Synthesis
        ic_memo = self._synthesize_ic_memo(
            extraction=extraction_result,
            analysis=analysis_result,
            risk=risk_result,
            valuation=valuation_result,
        )

        self._update_progress(
            phase="complete",
            percentage=100,
            message="Analysis complete!",
        )

        return ic_memo

    async def _run_extraction(
        self,
        images: Optional[list[Image.Image]],
        text_content: Optional[str],
        company_name_hint: Optional[str],
    ) -> ExtractionResult:
        """Run extraction agent."""
        logger.info("[ORCHESTRATOR] Phase 1: Extraction")

        return await self.extraction_agent.run(
            images=images,
            text_content=text_content,
            company_name_hint=company_name_hint,
        )

    async def _run_parallel_analysis(
        self,
        extraction_result: ExtractionResult,
        fast_mode: bool,
    ) -> tuple[AnalysisResult, RiskResult, ValuationResult]:
        """Run analysis, risk, and valuation agents in parallel."""
        logger.info("[ORCHESTRATOR] Phase 2: Parallel Analysis")

        # Create tasks for parallel execution
        tasks = [
            self._run_with_status(
                "Analysis",
                self.analysis_agent.run(extraction_result=extraction_result),
            ),
            self._run_with_status(
                "Risk",
                self.risk_agent.run(extraction_result=extraction_result),
            ),
            self._run_with_status(
                "Valuation",
                self.valuation_agent.run(
                    extraction_result=extraction_result,
                    analysis_result=None,  # Will use extraction only for now
                ),
            ),
        ]

        # Run all in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle results
        analysis_result = self._handle_result(results[0], "Analysis", AnalysisResult)
        risk_result = self._handle_result(results[1], "Risk", RiskResult)
        valuation_result = self._handle_result(results[2], "Valuation", ValuationResult)

        # If valuation needs analysis data, re-run with it
        if analysis_result and isinstance(valuation_result, Exception):
            logger.info("[ORCHESTRATOR] Retrying valuation with analysis data...")
            try:
                valuation_result = await self.valuation_agent.run(
                    extraction_result=extraction_result,
                    analysis_result=analysis_result,
                )
            except Exception as e:
                logger.error(f"[ORCHESTRATOR] Valuation retry failed: {e}")
                valuation_result = self._create_fallback_valuation(extraction_result)

        return analysis_result, risk_result, valuation_result

    async def _run_with_status(
        self,
        name: str,
        coro: Any,
    ) -> Any:
        """Run a coroutine and track status."""
        start_time = time.time()
        logger.info(f"[ORCHESTRATOR] Starting {name} Agent...")

        try:
            result = await coro
            elapsed = time.time() - start_time
            logger.info(f"[ORCHESTRATOR] {name} Agent completed in {elapsed:.1f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"[ORCHESTRATOR] {name} Agent failed after {elapsed:.1f}s: {e}")
            raise

    def _handle_result(
        self,
        result: Any,
        name: str,
        expected_type: type,
    ) -> Any:
        """Handle agent result, creating fallback if needed."""
        if isinstance(result, Exception):
            logger.warning(
                f"[ORCHESTRATOR] {name} Agent failed, using fallback: {result}"
            )
            return self._create_fallback(name)
        elif isinstance(result, expected_type):
            return result
        else:
            logger.warning(
                f"[ORCHESTRATOR] {name} Agent returned unexpected type: {type(result)}"
            )
            return self._create_fallback(name)

    def _create_fallback(self, agent_name: str) -> Any:
        """Create fallback result for failed agent."""
        if agent_name == "Analysis":
            return self._create_fallback_analysis()
        elif agent_name == "Risk":
            return self._create_fallback_risk()
        elif agent_name == "Valuation":
            extraction = self.context.get("extraction")
            return self._create_fallback_valuation(extraction)
        return None

    def _create_fallback_analysis(self) -> AnalysisResult:
        """Create minimal analysis result."""
        from app.models.schemas import (
            BusinessModelScore,
            CompetitiveAnalysis,
            ConfidenceScore,
            GrowthAnalysis,
            InvestmentThesis,
            MarketAnalysis,
        )

        default_score = ConfidenceScore(
            score=5.0,
            confidence=ConfidenceLevel.LOW,
            reasoning="Analysis agent failed - using default values",
        )

        return AnalysisResult(
            business_model=BusinessModelScore(
                overall_score=default_score,
                revenue_quality=default_score,
                margin_structure=default_score,
                scalability=default_score,
                defensibility=default_score,
                capital_efficiency=default_score,
            ),
            market_analysis=MarketAnalysis(
                market_score=default_score,
                tam_validity=default_score,
                market_timing=default_score,
            ),
            competitive_analysis=CompetitiveAnalysis(
                competitive_score=default_score,
                differentiation_strength=default_score,
                barriers_to_entry=default_score,
            ),
            growth_analysis=GrowthAnalysis(
                growth_score=default_score,
                growth_sustainability=default_score,
            ),
            unit_economics_quality=default_score,
            team_assessment=default_score,
            investment_thesis=InvestmentThesis(
                thesis_statement="Analysis incomplete - manual review required",
                thesis_confidence=ConfidenceLevel.LOW,
            ),
            overall_attractiveness_score=default_score,
            analysis_confidence=0.2,
        )

    def _create_fallback_risk(self) -> RiskResult:
        """Create minimal risk result."""
        return RiskResult(
            overall_risk_score=5.0,
            risk_adjusted_recommendation=RecommendationType.MORE_DILIGENCE,
            recommendation_reasoning="Risk assessment incomplete - manual review required",
            assessment_confidence=0.2,
        )

    def _create_fallback_valuation(
        self,
        extraction: Optional[ExtractionResult],
    ) -> ValuationResult:
        """Create minimal valuation result."""
        from app.models.schemas import MonetaryValue

        # Estimate based on revenue if available
        base_value = 50.0  # Default $50M
        if extraction and extraction.financials.revenue:
            revenue = extraction.financials.revenue.normalized_amount
            base_value = revenue * 10 / 1_000_000  # 10x revenue

        return ValuationResult(
            valuation_range_low=MonetaryValue(amount=base_value * 0.7, unit="M"),
            valuation_range_mid=MonetaryValue(amount=base_value, unit="M"),
            valuation_range_high=MonetaryValue(amount=base_value * 1.3, unit="M"),
            probability_weighted_value=MonetaryValue(amount=base_value, unit="M"),
            valuation_confidence=ConfidenceLevel.LOW,
            key_valuation_risks=["Valuation analysis incomplete - estimates only"],
            methodologies_used=["Fallback Estimate"],
        )

    def _synthesize_ic_memo(
        self,
        extraction: ExtractionResult,
        analysis: AnalysisResult,
        risk: RiskResult,
        valuation: ValuationResult,
    ) -> ICMemo:
        """Synthesize all results into IC Memo."""
        logger.info("[ORCHESTRATOR] Phase 3: IC Memo Synthesis")

        # Determine final recommendation
        final_recommendation = self._determine_recommendation(analysis, risk, valuation)

        # Create executive summary
        executive_summary = self._create_executive_summary(
            extraction=extraction,
            analysis=analysis,
            risk=risk,
            valuation=valuation,
            recommendation=final_recommendation,
        )

        # Calculate total time
        total_time = (
            (datetime.utcnow() - self._started_at).total_seconds()
            if self._started_at
            else 0
        )

        # Determine conviction level
        conviction = self._determine_conviction(analysis, risk)

        # Collect diligence items
        diligence_items = self._collect_diligence_items(analysis, risk)

        return ICMemo(
            company_name=extraction.company_name,
            memo_date=datetime.utcnow(),
            executive_summary=executive_summary,
            extraction_result=extraction,
            analysis_result=analysis,
            risk_result=risk,
            valuation_result=valuation,
            final_recommendation=final_recommendation,
            conviction_level=conviction,
            diligence_items=diligence_items,
            key_questions_for_management=analysis.critical_questions[:5],
            total_processing_time_seconds=total_time,
        )

    def _determine_recommendation(
        self,
        analysis: AnalysisResult,
        risk: RiskResult,
        valuation: ValuationResult,
    ) -> RecommendationType:
        """Determine final investment recommendation."""
        # Start with risk-adjusted recommendation
        base_rec = risk.risk_adjusted_recommendation

        # Adjust based on analysis score
        score = analysis.overall_attractiveness_score.score

        # Upgrade if very attractive and risks manageable
        if score >= 7.5 and risk.critical_risks == 0:
            if base_rec == RecommendationType.INVEST:
                return RecommendationType.STRONG_INVEST
            elif base_rec == RecommendationType.CONDITIONAL_INVEST:
                return RecommendationType.INVEST

        # Downgrade if valuation is too high
        if valuation.implied_discount_premium < -0.3:
            if base_rec == RecommendationType.STRONG_INVEST:
                return RecommendationType.INVEST
            elif base_rec == RecommendationType.INVEST:
                return RecommendationType.CONDITIONAL_INVEST

        return base_rec

    def _determine_conviction(
        self,
        analysis: AnalysisResult,
        risk: RiskResult,
    ) -> ConfidenceLevel:
        """Determine conviction level in recommendation."""
        # Factors that increase conviction
        high_factors = 0
        if analysis.analysis_confidence >= 0.7:
            high_factors += 1
        if risk.assessment_confidence >= 0.7:
            high_factors += 1
        if risk.data_integrity_score >= 0.8:
            high_factors += 1
        if risk.critical_risks == 0:
            high_factors += 1

        if high_factors >= 3:
            return ConfidenceLevel.HIGH
        elif high_factors >= 1:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    def _create_executive_summary(
        self,
        extraction: ExtractionResult,
        analysis: AnalysisResult,
        risk: RiskResult,
        valuation: ValuationResult,
        recommendation: RecommendationType,
    ) -> ExecutiveSummary:
        """Create executive summary for memo."""
        # Company overview
        overview_parts = [extraction.company_name]
        if extraction.tagline:
            overview_parts.append(f"- {extraction.tagline}")
        if extraction.business_model:
            overview_parts.append(f"Business Model: {extraction.business_model}")
        if extraction.stage:
            overview_parts.append(f"Stage: {extraction.stage.value.replace('_', ' ').title()}")
        if extraction.financials.revenue:
            rev = extraction.financials.revenue
            overview_parts.append(f"Revenue: ${rev.amount}{rev.unit}")

        company_overview = " | ".join(overview_parts)

        # Investment highlights
        highlights = analysis.key_strengths[:5]

        # Key concerns
        concerns = risk.deal_breakers + analysis.key_weaknesses[:3]

        # Valuation summary
        val_summary = (
            f"Valuation Range: ${valuation.valuation_range_low.amount:.0f}M - "
            f"${valuation.valuation_range_high.amount:.0f}M "
            f"(Mid: ${valuation.valuation_range_mid.amount:.0f}M)"
        )
        if valuation.ask_vs_valuation:
            val_summary += f". {valuation.ask_vs_valuation}"

        # Next steps based on recommendation
        next_steps_map = {
            RecommendationType.STRONG_INVEST: [
                "Schedule management meeting",
                "Begin legal due diligence",
                "Prepare term sheet draft",
            ],
            RecommendationType.INVEST: [
                "Schedule management meeting",
                "Complete customer reference calls",
                "Review financial model in detail",
            ],
            RecommendationType.CONDITIONAL_INVEST: [
                "Address key risks before proceeding",
                "Request additional data/documentation",
                "Conduct deeper competitive analysis",
            ],
            RecommendationType.MORE_DILIGENCE: [
                "Request detailed financial model",
                "Conduct market research",
                "Complete background checks",
            ],
            RecommendationType.PASS: [
                "Send pass letter with feedback",
                "Keep in database for future reference",
            ],
            RecommendationType.STRONG_PASS: [
                "Send pass letter",
                "Document key concerns for record",
            ],
        }

        return ExecutiveSummary(
            company_overview=company_overview,
            investment_highlights=highlights,
            key_concerns=concerns[:5],
            recommendation=recommendation,
            recommendation_rationale=risk.recommendation_reasoning,
            valuation_summary=val_summary,
            next_steps=next_steps_map.get(recommendation, []),
        )

    def _collect_diligence_items(
        self,
        analysis: AnalysisResult,
        risk: RiskResult,
    ) -> list[str]:
        """Collect recommended diligence workstreams."""
        items: list[str] = []

        # Must verify from risk
        items.extend(risk.must_verify_items)

        # Add standard workstreams
        standard = [
            "Customer reference calls (3-5 customers)",
            "Management team background checks",
            "Financial model review and validation",
            "Legal document review (cap table, contracts)",
            "Technology/product deep dive",
        ]

        for item in standard:
            if item not in items:
                items.append(item)

        return items[:10]

    def _update_progress(
        self,
        phase: str,
        percentage: float,
        message: str,
    ) -> None:
        """Update and emit progress."""
        now = datetime.utcnow()
        elapsed = (now - self._started_at).total_seconds() if self._started_at else 0

        # Estimate completion
        if percentage > 0:
            estimated_total = elapsed / (percentage / 100)
            estimated_remaining = estimated_total - elapsed
            estimated_completion = now + timedelta(seconds=estimated_remaining)
        else:
            estimated_completion = None

        progress = OrchestratorProgress(
            overall_status=AgentStatus.RUNNING,
            current_phase=phase,
            progress_percentage=percentage,
            agents_status=[
                self.extraction_agent.execution_status,
                self.analysis_agent.execution_status,
                self.risk_agent.execution_status,
                self.valuation_agent.execution_status,
            ],
            started_at=self._started_at or now,
            estimated_completion=estimated_completion,
            messages=[message],
        )

        self._emit_progress(progress)
        logger.info(f"[ORCHESTRATOR] {percentage:.0f}% - {message}")

    @property
    def progress(self) -> Optional[OrchestratorProgress]:
        """Get current progress."""
        return self._current_progress
