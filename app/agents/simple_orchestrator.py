"""
Simplified Orchestrator for DealFlow AI Copilot.

Coordinates multi-file processing and agent execution with clean,
categorized output for each step.
"""

import time
from datetime import datetime
from typing import Any, Optional
from PIL import Image

from app.core.gemini_client import GeminiClient
from app.models.simple_output import (
    AnalysisOutput,
    CompanyBasics,
    DealSummary,
    ExtractionOutput,
    FinancialMetrics,
    FullAnalysisResult,
    MarketInfo,
    Recommendation,
    Risk,
    RiskLevel,
    RiskOutput,
    ScoreWithReasoning,
    TeamMember,
    ValuationMethod,
    ValuationOutput,
)
from app.models.quick_schema import QUICK_EXTRACTION_SCHEMA, QUICK_EXTRACTION_PROMPT
from app.services.multi_file_processor import CombinedContent, get_multi_file_processor
from app.utils.logger import logger


class SimpleOrchestrator:
    """
    Simplified orchestrator for deal analysis.

    Processes multiple files through a clear pipeline:
    1. Extract data from all documents
    2. Analyze business quality
    3. Assess risks
    4. Calculate valuation
    5. Generate summary

    Each step produces clearly categorized output with methodology explanation.

    Example:
        ```python
        orchestrator = SimpleOrchestrator()

        # Analyze from file paths
        result = await orchestrator.analyze_files([
            "pitch_deck.pdf",
            "financials.xlsx"
        ])

        # Or from bytes
        result = await orchestrator.analyze_bytes([
            ("pitch.pdf", pdf_bytes),
            ("data.xlsx", xlsx_bytes)
        ])

        print(f"Recommendation: {result.summary.recommendation}")
        print(f"Valuation: {result.summary.valuation_range}")
        ```
    """

    def __init__(self):
        """Initialize the orchestrator."""
        self.client = GeminiClient()
        self.processor = get_multi_file_processor()
        logger.info("SimpleOrchestrator initialized")

    async def analyze_files(
        self,
        file_paths: list[str],
        company_name_hint: Optional[str] = None,
    ) -> FullAnalysisResult:
        """
        Analyze multiple files by path.

        Args:
            file_paths: List of file paths to analyze
            company_name_hint: Optional company name hint

        Returns:
            FullAnalysisResult with all agent outputs
        """
        start_time = time.time()
        logger.info(f"Starting analysis of {len(file_paths)} files")

        # Step 1: Process all files
        content = await self.processor.process_files(file_paths)

        # Step 2: Run analysis pipeline
        result = await self._run_pipeline(content, company_name_hint)

        # Add processing time and file info
        result.total_processing_time_seconds = time.time() - start_time
        result.documents_analyzed = [p.split("/")[-1].split("\\")[-1] for p in file_paths]

        logger.info(f"Analysis complete in {result.total_processing_time_seconds:.1f}s")
        return result

    async def analyze_bytes(
        self,
        files: list[tuple[str, bytes]],
        company_name_hint: Optional[str] = None,
    ) -> FullAnalysisResult:
        """
        Analyze multiple files from bytes.

        Args:
            files: List of (filename, content_bytes) tuples
            company_name_hint: Optional company name hint

        Returns:
            FullAnalysisResult with all agent outputs
        """
        start_time = time.time()
        logger.info(f"Starting analysis of {len(files)} files from bytes")

        # Step 1: Process all files
        content = await self.processor.process_file_bytes(files)

        # Step 2: Run analysis pipeline
        result = await self._run_pipeline(content, company_name_hint)

        # Add processing time and file info
        result.total_processing_time_seconds = time.time() - start_time
        result.documents_analyzed = [f[0] for f in files]

        logger.info(f"Analysis complete in {result.total_processing_time_seconds:.1f}s")
        return result

    async def _run_pipeline(
        self,
        content: CombinedContent,
        company_name_hint: Optional[str] = None,
    ) -> FullAnalysisResult:
        """Run the full analysis pipeline."""

        # Step 1: Extract data
        logger.info("Step 1/5: Extracting data from documents...")
        extraction = await self._extract(content, company_name_hint)

        # Step 2: Analyze business
        logger.info("Step 2/5: Analyzing business model...")
        analysis = await self._analyze(extraction)

        # Step 3: Assess risks
        logger.info("Step 3/5: Assessing risks...")
        risks = await self._assess_risks(extraction)

        # Step 4: Calculate valuation
        logger.info("Step 4/5: Calculating valuation...")
        valuation = await self._value(extraction, analysis, risks)

        # Step 5: Generate summary
        logger.info("Step 5/5: Generating summary...")
        summary = await self._summarize(extraction, analysis, risks, valuation)

        return FullAnalysisResult(
            summary=summary,
            extraction=extraction,
            analysis=analysis,
            risks=risks,
            valuation=valuation,
            total_processing_time_seconds=0,  # Will be set by caller
            documents_analyzed=[],
        )

    async def _extract(
        self,
        content: CombinedContent,
        company_name_hint: Optional[str] = None,
    ) -> ExtractionOutput:
        """Extract structured data from combined content."""

        # Use quick extraction schema for speed
        prompt = QUICK_EXTRACTION_PROMPT.format(content=content.combined_text[:30000])
        if company_name_hint:
            prompt = f"Note: The company name is likely '{company_name_hint}'.\n\n" + prompt

        try:
            data = await self.client.generate_structured(
                prompt=prompt,
                response_schema=QUICK_EXTRACTION_SCHEMA,
                model="flash",
                temperature=0.1,
            )
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            data = {"company_name": company_name_hint or "Unknown Company"}

        # Build extraction output
        return ExtractionOutput(
            company=CompanyBasics(
                name=data.get("company_name", company_name_hint or "Unknown"),
                tagline=data.get("tagline"),
                industry=data.get("industry"),
                stage=data.get("stage"),
                business_model=data.get("business_model"),
                founded_year=data.get("founded_year"),
                headquarters=data.get("headquarters"),
            ),
            financials=FinancialMetrics(
                revenue_arr=data.get("revenue_arr_millions"),
                growth_rate=data.get("growth_rate_percent"),
                gross_margin=data.get("gross_margin_percent"),
                burn_rate=data.get("burn_rate_millions"),
                runway_months=data.get("runway_months"),
                total_raised=data.get("total_raised_millions"),
                asking_amount=data.get("asking_amount_millions"),
                valuation_ask=data.get("pre_money_valuation_millions"),
            ),
            team=[
                TeamMember(name=name)
                for name in (data.get("founder_names") or [])
            ],
            team_size=data.get("team_size"),
            market=MarketInfo(
                tam=data.get("tam_billions"),
                target_customers=None,
                competitors=[],
            ),
            documents_processed=len(content.documents),
            extraction_confidence=0.75,
            data_gaps=self._identify_data_gaps(data),
        )

    def _identify_data_gaps(self, data: dict) -> list[str]:
        """Identify missing data points."""
        gaps = []
        required_fields = [
            ("revenue_arr_millions", "Revenue/ARR"),
            ("growth_rate_percent", "Growth Rate"),
            ("gross_margin_percent", "Gross Margin"),
            ("burn_rate_millions", "Burn Rate"),
            ("runway_months", "Runway"),
            ("tam_billions", "TAM"),
            ("team_size", "Team Size"),
        ]
        for field, label in required_fields:
            if data.get(field) is None:
                gaps.append(f"Missing: {label}")
        return gaps

    async def _analyze(self, extraction: ExtractionOutput) -> AnalysisOutput:
        """Analyze business quality."""

        prompt = f"""Analyze this company and provide scores (0-10) for each dimension.

COMPANY DATA:
- Name: {extraction.company.name}
- Industry: {extraction.company.industry or 'Unknown'}
- Stage: {extraction.company.stage or 'Unknown'}
- Business Model: {extraction.company.business_model or 'Unknown'}
- ARR: ${extraction.financials.revenue_arr or 0}M
- Growth: {extraction.financials.growth_rate or 0}%
- Gross Margin: {extraction.financials.gross_margin or 0}%
- TAM: ${extraction.market.tam or 0}B
- Team Size: {extraction.team_size or 'Unknown'}

Provide a JSON response with:
- business_model_score: number 0-10 and reasoning string
- market_score: number 0-10 and reasoning string
- competitive_score: number 0-10 and reasoning string
- growth_score: number 0-10 and reasoning string
- strengths: array of 3 key strengths
- weaknesses: array of 3 key weaknesses
- opportunities: array of 2-3 opportunities
- threats: array of 2-3 threats

IMPORTANT: All scores must be NUMBERS between 0 and 10. Reasoning must be strings."""

        schema = {
            "type": "object",
            "properties": {
                "business_model_score": {"type": "number"},
                "business_model_reasoning": {"type": "string"},
                "market_score": {"type": "number"},
                "market_reasoning": {"type": "string"},
                "competitive_score": {"type": "number"},
                "competitive_reasoning": {"type": "string"},
                "growth_score": {"type": "number"},
                "growth_reasoning": {"type": "string"},
                "strengths": {"type": "array", "items": {"type": "string"}},
                "weaknesses": {"type": "array", "items": {"type": "string"}},
                "opportunities": {"type": "array", "items": {"type": "string"}},
                "threats": {"type": "array", "items": {"type": "string"}},
            }
        }

        try:
            data = await self.client.generate_structured(
                prompt=prompt,
                response_schema=schema,
                model="flash",
                temperature=0.2,
            )
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            data = {}

        # Calculate overall score
        scores = [
            data.get("business_model_score", 5),
            data.get("market_score", 5),
            data.get("competitive_score", 5),
            data.get("growth_score", 5),
        ]
        overall = sum(scores) / len(scores)

        return AnalysisOutput(
            business_model_score=ScoreWithReasoning(
                score=float(data.get("business_model_score", 5)),
                reasoning=data.get("business_model_reasoning", "Insufficient data"),
            ),
            market_score=ScoreWithReasoning(
                score=float(data.get("market_score", 5)),
                reasoning=data.get("market_reasoning", "Insufficient data"),
            ),
            competitive_score=ScoreWithReasoning(
                score=float(data.get("competitive_score", 5)),
                reasoning=data.get("competitive_reasoning", "Insufficient data"),
            ),
            growth_score=ScoreWithReasoning(
                score=float(data.get("growth_score", 5)),
                reasoning=data.get("growth_reasoning", "Insufficient data"),
            ),
            overall_score=overall,
            strengths=data.get("strengths", [])[:3],
            weaknesses=data.get("weaknesses", [])[:3],
            opportunities=data.get("opportunities", [])[:3],
            threats=data.get("threats", [])[:3],
        )

    async def _assess_risks(self, extraction: ExtractionOutput) -> RiskOutput:
        """Assess risks across categories."""

        prompt = f"""Identify key risks for this company.

COMPANY DATA:
- Name: {extraction.company.name}
- Stage: {extraction.company.stage or 'Unknown'}
- ARR: ${extraction.financials.revenue_arr or 0}M
- Growth: {extraction.financials.growth_rate or 0}%
- Burn Rate: ${extraction.financials.burn_rate or 0}M/month
- Runway: {extraction.financials.runway_months or 'Unknown'} months
- Team Size: {extraction.team_size or 'Unknown'}
- Data Gaps: {', '.join(extraction.data_gaps) if extraction.data_gaps else 'None'}

Identify 4-8 risks across these categories: financial, team, market, operational.

Return a JSON object with:
- risks: array of objects, each with:
  - category: "financial" | "team" | "market" | "operational"
  - title: short risk title
  - description: 1-2 sentence description
  - severity: "critical" | "high" | "medium" | "low"
  - likelihood: "high" | "medium" | "low"
  - mitigation: optional suggestion
- overall_risk_score: number 0-10 (0=low risk, 10=high risk)
- deal_breakers: array of critical issues that could stop the deal
- must_verify: array of items to check in due diligence"""

        schema = {
            "type": "object",
            "properties": {
                "risks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string"},
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "severity": {"type": "string"},
                            "likelihood": {"type": "string"},
                            "mitigation": {"type": "string"},
                        }
                    }
                },
                "overall_risk_score": {"type": "number"},
                "deal_breakers": {"type": "array", "items": {"type": "string"}},
                "must_verify": {"type": "array", "items": {"type": "string"}},
            }
        }

        try:
            data = await self.client.generate_structured(
                prompt=prompt,
                response_schema=schema,
                model="flash",
                temperature=0.2,
            )
        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            data = {"risks": [], "overall_risk_score": 5}

        # Parse risks
        risks = []
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for r in data.get("risks", []):
            severity = r.get("severity", "medium").lower()
            if severity not in severity_counts:
                severity = "medium"

            severity_counts[severity] += 1

            risks.append(Risk(
                category=r.get("category", "operational"),
                title=r.get("title", "Unknown Risk"),
                description=r.get("description", ""),
                severity=RiskLevel(severity),
                likelihood=r.get("likelihood", "medium"),
                mitigation=r.get("mitigation"),
            ))

        return RiskOutput(
            risks=risks,
            critical_count=severity_counts["critical"],
            high_count=severity_counts["high"],
            medium_count=severity_counts["medium"],
            low_count=severity_counts["low"],
            overall_risk_score=float(data.get("overall_risk_score", 5)),
            deal_breakers=data.get("deal_breakers", []),
            must_verify=data.get("must_verify", []),
        )

    async def _value(
        self,
        extraction: ExtractionOutput,
        analysis: AnalysisOutput,
        risks: RiskOutput,
    ) -> ValuationOutput:
        """Calculate valuation using multiple methods."""

        arr = extraction.financials.revenue_arr or 0
        growth = extraction.financials.growth_rate or 0
        margin = extraction.financials.gross_margin or 70
        ask = extraction.financials.valuation_ask

        prompt = f"""Calculate valuation for this company.

COMPANY DATA:
- ARR: ${arr}M
- Growth Rate: {growth}%
- Gross Margin: {margin}%
- Stage: {extraction.company.stage or 'Series A'}
- Business Model: {extraction.company.business_model or 'SaaS'}
- Analysis Score: {analysis.overall_score}/10
- Risk Score: {risks.overall_risk_score}/10 (higher = more risk)
- Company's Asking Valuation: ${ask or 'Not specified'}M

Provide valuations using three methods:

1. REVENUE MULTIPLE METHOD:
   - For SaaS: Use ARR multiples based on growth rate
   - High growth (>100%): 15-25x ARR
   - Strong growth (50-100%): 10-15x ARR
   - Moderate growth (25-50%): 5-10x ARR

2. COMPARABLE METHOD:
   - Based on similar stage companies' recent rounds
   - Adjust for growth and quality

3. SCENARIO METHOD:
   - Bull case (20% probability): Things go well
   - Base case (60% probability): Meets expectations
   - Bear case (20% probability): Challenges emerge

Return JSON with:
- revenue_multiple_low, revenue_multiple_mid, revenue_multiple_high: numbers in millions
- comparable_low, comparable_mid, comparable_high: numbers in millions
- scenario_low, scenario_mid, scenario_high: numbers in millions
- final_low, final_mid, final_high: weighted average in millions
- reasoning: brief explanation

All values must be NUMBERS (in millions USD)."""

        schema = {
            "type": "object",
            "properties": {
                "revenue_multiple_low": {"type": "number"},
                "revenue_multiple_mid": {"type": "number"},
                "revenue_multiple_high": {"type": "number"},
                "comparable_low": {"type": "number"},
                "comparable_mid": {"type": "number"},
                "comparable_high": {"type": "number"},
                "scenario_low": {"type": "number"},
                "scenario_mid": {"type": "number"},
                "scenario_high": {"type": "number"},
                "final_low": {"type": "number"},
                "final_mid": {"type": "number"},
                "final_high": {"type": "number"},
                "reasoning": {"type": "string"},
            }
        }

        try:
            data = await self.client.generate_structured(
                prompt=prompt,
                response_schema=schema,
                model="flash",
                temperature=0.2,
            )
        except Exception as e:
            logger.error(f"Valuation failed: {e}")
            # Provide rough estimate
            base_val = arr * 10 if arr > 0 else 50
            data = {
                "final_low": base_val * 0.7,
                "final_mid": base_val,
                "final_high": base_val * 1.5,
            }

        # Build valuation methods
        methods = []

        if data.get("revenue_multiple_mid"):
            methods.append(ValuationMethod(
                method_name="Revenue Multiple",
                value_low=float(data.get("revenue_multiple_low", 0)),
                value_mid=float(data.get("revenue_multiple_mid", 0)),
                value_high=float(data.get("revenue_multiple_high", 0)),
                key_assumptions=[
                    f"ARR: ${arr}M",
                    f"Growth: {growth}%",
                    f"Implied multiple: {data.get('revenue_multiple_mid', 0) / arr:.1f}x" if arr > 0 else "N/A",
                ],
            ))

        if data.get("comparable_mid"):
            methods.append(ValuationMethod(
                method_name="Comparable Analysis",
                value_low=float(data.get("comparable_low", 0)),
                value_mid=float(data.get("comparable_mid", 0)),
                value_high=float(data.get("comparable_high", 0)),
                key_assumptions=["Based on similar stage companies", "Adjusted for growth profile"],
            ))

        if data.get("scenario_mid"):
            methods.append(ValuationMethod(
                method_name="Scenario Analysis",
                value_low=float(data.get("scenario_low", 0)),
                value_mid=float(data.get("scenario_mid", 0)),
                value_high=float(data.get("scenario_high", 0)),
                key_assumptions=["Bull case: 20% probability", "Base case: 60% probability", "Bear case: 20% probability"],
            ))

        # Final values
        final_low = float(data.get("final_low", 0))
        final_mid = float(data.get("final_mid", 0))
        final_high = float(data.get("final_high", 0))

        # Compare to ask
        ask_comparison = None
        premium_discount = None
        if ask and final_mid > 0:
            premium_discount = ((ask - final_mid) / final_mid) * 100
            if premium_discount > 20:
                ask_comparison = "Expensive"
            elif premium_discount < -20:
                ask_comparison = "Attractive"
            else:
                ask_comparison = "Fair"

        return ValuationOutput(
            methods=methods,
            valuation_low=final_low,
            valuation_mid=final_mid,
            valuation_high=final_high,
            company_ask=ask,
            ask_vs_our_value=ask_comparison,
            premium_discount_pct=premium_discount,
        )

    async def _summarize(
        self,
        extraction: ExtractionOutput,
        analysis: AnalysisOutput,
        risks: RiskOutput,
        valuation: ValuationOutput,
    ) -> DealSummary:
        """Generate executive summary."""

        # Determine recommendation
        avg_score = (analysis.overall_score * 0.6 + (10 - risks.overall_risk_score) * 0.4)

        if risks.critical_count > 0:
            recommendation = Recommendation.PASS
            conviction = "High"
        elif avg_score >= 7.5:
            recommendation = Recommendation.STRONG_BUY
            conviction = "High"
        elif avg_score >= 6.5:
            recommendation = Recommendation.BUY
            conviction = "Medium"
        elif avg_score >= 5:
            recommendation = Recommendation.HOLD
            conviction = "Medium"
        else:
            recommendation = Recommendation.PASS
            conviction = "Medium"

        # Generate headline
        arr = extraction.financials.revenue_arr
        growth = extraction.financials.growth_rate

        if arr and growth:
            headline = f"{extraction.company.name}: ${arr}M ARR, {growth}% growth, {extraction.company.stage or 'early stage'} {extraction.company.business_model or 'company'}"
        else:
            headline = f"{extraction.company.name}: {extraction.company.stage or 'Early stage'} {extraction.company.industry or 'technology'} company"

        # Key metrics
        key_metrics = {}
        if arr:
            key_metrics["ARR"] = f"${arr}M"
        if growth:
            key_metrics["Growth"] = f"{growth}%"
        if extraction.financials.gross_margin:
            key_metrics["Gross Margin"] = f"{extraction.financials.gross_margin}%"
        if extraction.financials.runway_months:
            key_metrics["Runway"] = f"{extraction.financials.runway_months} months"
        if valuation.valuation_mid:
            key_metrics["Valuation (Our Estimate)"] = f"${valuation.valuation_mid:.0f}M"

        # Reasons to invest
        reasons = []
        if growth and growth > 100:
            reasons.append(f"Strong growth at {growth}% YoY")
        if extraction.financials.gross_margin and extraction.financials.gross_margin > 70:
            reasons.append(f"Healthy gross margins of {extraction.financials.gross_margin}%")
        if extraction.market.tam and extraction.market.tam > 10:
            reasons.append(f"Large market opportunity (${extraction.market.tam}B TAM)")

        reasons.extend(analysis.strengths[:3 - len(reasons)])

        # Key concerns
        concerns = analysis.weaknesses[:2]
        if risks.deal_breakers:
            concerns.extend(risks.deal_breakers[:1])

        # Valuation range string
        if valuation.valuation_low and valuation.valuation_high:
            val_range = f"${valuation.valuation_low:.0f}M - ${valuation.valuation_high:.0f}M"
        else:
            val_range = "Unable to calculate"

        return DealSummary(
            company_name=extraction.company.name,
            headline=headline,
            recommendation=recommendation,
            conviction=conviction,
            key_metrics=key_metrics,
            analysis_score=analysis.overall_score,
            risk_score=risks.overall_risk_score,
            reasons_to_invest=reasons[:3],
            key_concerns=concerns[:3],
            valuation_range=val_range,
            valuation_vs_ask=valuation.ask_vs_our_value,
            diligence_priorities=risks.must_verify[:5],
            questions_for_founders=[
                "What are your biggest challenges in scaling?",
                "How do you differentiate from competitors?",
                "What's your path to profitability?",
            ],
        )


# Convenience function
def get_simple_orchestrator() -> SimpleOrchestrator:
    """Get a SimpleOrchestrator instance."""
    return SimpleOrchestrator()
