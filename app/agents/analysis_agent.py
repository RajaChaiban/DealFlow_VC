"""
Analysis Agent for DealFlow AI Copilot.

Performs deep business evaluation across multiple dimensions:
- Business model viability
- Market opportunity assessment
- Competitive positioning
- Unit economics quality
- Growth trajectory analysis
- Team assessment

Synthesizes findings into an investment thesis with confidence scores.
"""

import json
from typing import Any, Optional

from app.agents.base import BaseAgent
from app.models.schemas import (
    AnalysisResult,
    BusinessModelScore,
    ComparableCompany,
    CompetitiveAnalysis,
    ConfidenceLevel,
    ConfidenceScore,
    ExtractionResult,
    GrowthAnalysis,
    InvestmentThesis,
    MarketAnalysis,
    MonetaryValue,
)
from app.utils.logger import logger

# Import prompts
import sys
sys.path.insert(0, ".")
from prompts.analysis_prompts import (
    ANALYSIS_SYSTEM_PROMPT,
    BUSINESS_MODEL_ANALYSIS_PROMPT,
    COMPETITIVE_ANALYSIS_PROMPT,
    GROWTH_ANALYSIS_PROMPT,
    INVESTMENT_THESIS_PROMPT,
    MARKET_ANALYSIS_PROMPT,
    TEAM_ASSESSMENT_PROMPT,
)


class AnalysisAgent(BaseAgent[AnalysisResult]):
    """
    Agent responsible for comprehensive business analysis.

    Evaluates:
    - Business model quality and sustainability
    - Market opportunity and timing
    - Competitive positioning and moats
    - Growth trajectory and drivers
    - Team capabilities

    Example:
        ```python
        agent = AnalysisAgent()
        result = await agent.run(extraction_result=extraction_data)
        print(result.investment_thesis.thesis_statement)
        print(result.overall_attractiveness_score.score)
        ```
    """

    @property
    def name(self) -> str:
        return "AnalysisAgent"

    async def execute(
        self,
        extraction_result: ExtractionResult,
    ) -> AnalysisResult:
        """
        Execute comprehensive business analysis.

        Args:
            extraction_result: Extracted data from pitch deck

        Returns:
            AnalysisResult with all assessments and investment thesis

        Raises:
            AnalysisError: If analysis fails
        """
        logger.info(f"[{self.name}] Starting analysis for {extraction_result.company_name}")

        # Convert extraction to JSON for prompts
        extraction_json = extraction_result.model_dump_json(indent=2)

        # Step 1: Business model analysis
        logger.debug(f"[{self.name}] Analyzing business model...")
        business_model = await self._analyze_business_model(extraction_json)

        # Step 2: Market analysis
        logger.debug(f"[{self.name}] Analyzing market opportunity...")
        market_analysis = await self._analyze_market(extraction_json)

        # Step 3: Competitive analysis
        logger.debug(f"[{self.name}] Analyzing competitive positioning...")
        competitive_analysis = await self._analyze_competitive(extraction_json)

        # Step 4: Growth analysis
        logger.debug(f"[{self.name}] Analyzing growth trajectory...")
        growth_analysis = await self._analyze_growth(extraction_json)

        # Step 5: Team assessment
        logger.debug(f"[{self.name}] Assessing team...")
        team_score = await self._assess_team(extraction_result.team.model_dump_json())

        # Step 6: Unit economics assessment
        unit_economics_score = self._assess_unit_economics(extraction_result)

        # Step 7: Investment thesis synthesis
        logger.debug(f"[{self.name}] Synthesizing investment thesis...")
        thesis_data = await self._synthesize_thesis(
            extraction_json=extraction_json,
            business_model=business_model,
            market_analysis=market_analysis,
            competitive_analysis=competitive_analysis,
            growth_analysis=growth_analysis,
        )

        # Build final result
        result = self._build_result(
            business_model=business_model,
            market_analysis=market_analysis,
            competitive_analysis=competitive_analysis,
            growth_analysis=growth_analysis,
            team_score=team_score,
            unit_economics_score=unit_economics_score,
            thesis_data=thesis_data,
        )

        logger.info(
            f"[{self.name}] Analysis complete: "
            f"Overall score {result.overall_attractiveness_score.score}/10"
        )

        return result

    async def _analyze_business_model(
        self,
        extraction_json: str,
    ) -> BusinessModelScore:
        """Analyze business model quality."""
        prompt = BUSINESS_MODEL_ANALYSIS_PROMPT.format(extraction_data=extraction_json)

        response = await self.client.generate_structured(
            prompt=prompt,
            response_schema=self._get_business_model_schema(),
            model="pro",
            temperature=0.2,
        )

        return BusinessModelScore(
            overall_score=self._build_confidence_score(response.get("overall_score", {})),
            revenue_quality=self._build_confidence_score(response.get("revenue_quality", {})),
            margin_structure=self._build_confidence_score(response.get("margin_structure", {})),
            scalability=self._build_confidence_score(response.get("scalability", {})),
            defensibility=self._build_confidence_score(response.get("defensibility", {})),
            capital_efficiency=self._build_confidence_score(response.get("capital_efficiency", {})),
        )

    async def _analyze_market(
        self,
        extraction_json: str,
    ) -> MarketAnalysis:
        """Analyze market opportunity."""
        prompt = MARKET_ANALYSIS_PROMPT.format(extraction_data=extraction_json)

        response = await self.client.generate_structured(
            prompt=prompt,
            response_schema=self._get_market_schema(),
            model="pro",
            temperature=0.2,
        )

        return MarketAnalysis(
            market_score=self._build_confidence_score(response.get("market_score", {})),
            tam_validity=self._build_confidence_score(response.get("tam_validity", {})),
            market_timing=self._build_confidence_score(response.get("market_timing", {})),
            market_dynamics=response.get("market_dynamics"),
            tailwinds=response.get("tailwinds", []),
            headwinds=response.get("headwinds", []),
        )

    async def _analyze_competitive(
        self,
        extraction_json: str,
    ) -> CompetitiveAnalysis:
        """Analyze competitive positioning."""
        prompt = COMPETITIVE_ANALYSIS_PROMPT.format(extraction_data=extraction_json)

        response = await self.client.generate_structured(
            prompt=prompt,
            response_schema=self._get_competitive_schema(),
            model="pro",
            temperature=0.2,
        )

        return CompetitiveAnalysis(
            competitive_score=self._build_confidence_score(response.get("competitive_score", {})),
            market_position=response.get("market_position"),
            differentiation_strength=self._build_confidence_score(
                response.get("differentiation_strength", {})
            ),
            barriers_to_entry=self._build_confidence_score(response.get("barriers_to_entry", {})),
            competitive_threats=response.get("competitive_threats", []),
            sustainable_advantages=response.get("sustainable_advantages", []),
        )

    async def _analyze_growth(
        self,
        extraction_json: str,
    ) -> GrowthAnalysis:
        """Analyze growth trajectory."""
        prompt = GROWTH_ANALYSIS_PROMPT.format(extraction_data=extraction_json)

        response = await self.client.generate_structured(
            prompt=prompt,
            response_schema=self._get_growth_schema(),
            model="pro",
            temperature=0.2,
        )

        return GrowthAnalysis(
            growth_score=self._build_confidence_score(response.get("growth_score", {})),
            historical_growth_rate=response.get("historical_growth_rate"),
            projected_growth_rate=response.get("projected_growth_rate"),
            growth_drivers=response.get("growth_drivers", []),
            growth_constraints=response.get("growth_constraints", []),
            growth_sustainability=self._build_confidence_score(
                response.get("growth_sustainability", {})
            ),
        )

    async def _assess_team(
        self,
        team_json: str,
    ) -> ConfidenceScore:
        """Assess team quality."""
        prompt = TEAM_ASSESSMENT_PROMPT.format(team_data=team_json)

        response = await self.client.generate_structured(
            prompt=prompt,
            response_schema={
                "type": "object",
                "properties": {
                    "team_score": {"type": "object"},
                    "founder_assessment": {"type": "string"},
                    "team_gaps": {"type": "array"},
                    "team_strengths": {"type": "array"},
                    "concerns": {"type": "array"},
                },
            },
            model="pro",
            temperature=0.2,
        )

        return self._build_confidence_score(response.get("team_score", {}))

    def _assess_unit_economics(
        self,
        extraction: ExtractionResult,
    ) -> ConfidenceScore:
        """Assess unit economics quality based on extracted data."""
        score = 5.0  # Start at neutral
        reasoning_parts: list[str] = []

        ue = extraction.unit_economics

        # LTV/CAC ratio assessment
        if ue.ltv_cac_ratio:
            if ue.ltv_cac_ratio >= 3.0:
                score += 2.0
                reasoning_parts.append(f"Strong LTV/CAC of {ue.ltv_cac_ratio:.1f}x")
            elif ue.ltv_cac_ratio >= 2.0:
                score += 1.0
                reasoning_parts.append(f"Healthy LTV/CAC of {ue.ltv_cac_ratio:.1f}x")
            elif ue.ltv_cac_ratio < 1.0:
                score -= 2.0
                reasoning_parts.append(f"Concerning LTV/CAC of {ue.ltv_cac_ratio:.1f}x")
        else:
            score -= 0.5
            reasoning_parts.append("LTV/CAC not provided")

        # Payback period
        if ue.payback_period_months:
            if ue.payback_period_months <= 12:
                score += 1.5
                reasoning_parts.append(f"Fast payback of {ue.payback_period_months} months")
            elif ue.payback_period_months <= 18:
                score += 0.5
                reasoning_parts.append(f"Acceptable payback of {ue.payback_period_months} months")
            else:
                score -= 1.0
                reasoning_parts.append(f"Long payback of {ue.payback_period_months} months")

        # Net revenue retention (for SaaS)
        if ue.net_revenue_retention:
            if ue.net_revenue_retention >= 1.2:
                score += 1.5
                reasoning_parts.append(f"Excellent NRR of {ue.net_revenue_retention:.0%}")
            elif ue.net_revenue_retention >= 1.0:
                score += 0.5
                reasoning_parts.append(f"Good NRR of {ue.net_revenue_retention:.0%}")
            else:
                score -= 1.0
                reasoning_parts.append(f"Below-average NRR of {ue.net_revenue_retention:.0%}")

        # Churn rate
        if ue.churn_rate:
            if ue.churn_rate <= 0.02:
                score += 1.0
                reasoning_parts.append(f"Low churn of {ue.churn_rate:.1%}/month")
            elif ue.churn_rate >= 0.05:
                score -= 1.5
                reasoning_parts.append(f"High churn of {ue.churn_rate:.1%}/month")

        # Clamp score
        score = max(0.0, min(10.0, score))

        # Determine confidence
        confidence = ConfidenceLevel.MEDIUM
        if ue.ltv_cac_ratio and ue.payback_period_months:
            confidence = ConfidenceLevel.HIGH
        elif not ue.ltv_cac_ratio and not ue.payback_period_months:
            confidence = ConfidenceLevel.LOW

        return ConfidenceScore(
            score=score,
            confidence=confidence,
            reasoning="; ".join(reasoning_parts) if reasoning_parts else "Limited unit economics data",
        )

    async def _synthesize_thesis(
        self,
        extraction_json: str,
        business_model: BusinessModelScore,
        market_analysis: MarketAnalysis,
        competitive_analysis: CompetitiveAnalysis,
        growth_analysis: GrowthAnalysis,
    ) -> dict[str, Any]:
        """Synthesize investment thesis from all analyses."""
        prompt = INVESTMENT_THESIS_PROMPT.format(
            extraction_data=extraction_json,
            business_model_analysis=business_model.model_dump_json(),
            market_analysis=market_analysis.model_dump_json(),
            competitive_analysis=competitive_analysis.model_dump_json(),
            growth_analysis=growth_analysis.model_dump_json(),
        )

        return await self.client.generate_structured(
            prompt=prompt,
            response_schema=self._get_thesis_schema(),
            model="pro",
            temperature=0.3,
        )

    def _build_result(
        self,
        business_model: BusinessModelScore,
        market_analysis: MarketAnalysis,
        competitive_analysis: CompetitiveAnalysis,
        growth_analysis: GrowthAnalysis,
        team_score: ConfidenceScore,
        unit_economics_score: ConfidenceScore,
        thesis_data: dict[str, Any],
    ) -> AnalysisResult:
        """Build final AnalysisResult from components."""
        # Build investment thesis
        thesis_dict = thesis_data.get("investment_thesis", {})
        confidence_str = thesis_dict.get("thesis_confidence", "medium").lower()
        thesis_confidence = {
            "high": ConfidenceLevel.HIGH,
            "medium": ConfidenceLevel.MEDIUM,
            "low": ConfidenceLevel.LOW,
        }.get(confidence_str, ConfidenceLevel.MEDIUM)

        investment_thesis = InvestmentThesis(
            thesis_statement=thesis_dict.get("thesis_statement", ""),
            key_beliefs=thesis_dict.get("key_beliefs", []),
            upside_drivers=thesis_dict.get("upside_drivers", []),
            key_concerns=thesis_dict.get("key_concerns", []),
            thesis_confidence=thesis_confidence,
        )

        # Build comparable companies
        comparables = []
        for comp in thesis_data.get("comparable_companies", []):
            if isinstance(comp, dict):
                val = comp.get("valuation_at_similar_stage", {})
                comparables.append(
                    ComparableCompany(
                        name=comp.get("name", ""),
                        similarity_score=comp.get("similarity_score", 0.5),
                        outcome=comp.get("outcome"),
                        valuation_at_similar_stage=MonetaryValue(
                            amount=val.get("amount", 0),
                            unit=val.get("unit", "M"),
                        ) if val else None,
                        key_similarities=comp.get("key_similarities", []),
                        key_differences=comp.get("key_differences", []),
                    )
                )

        # Build overall score
        overall_score = self._build_confidence_score(
            thesis_data.get("overall_attractiveness_score", {})
        )

        # Calculate analysis confidence
        scores = [
            business_model.overall_score.score,
            market_analysis.market_score.score,
            competitive_analysis.competitive_score.score,
            growth_analysis.growth_score.score,
        ]
        avg_score = sum(scores) / len(scores) if scores else 5.0

        return AnalysisResult(
            business_model=business_model,
            market_analysis=market_analysis,
            competitive_analysis=competitive_analysis,
            growth_analysis=growth_analysis,
            unit_economics_quality=unit_economics_score,
            team_assessment=team_score,
            investment_thesis=investment_thesis,
            comparable_companies=comparables,
            overall_attractiveness_score=overall_score,
            key_strengths=thesis_data.get("key_strengths", []),
            key_weaknesses=thesis_data.get("key_weaknesses", []),
            critical_questions=thesis_data.get("critical_questions", []),
            analysis_confidence=avg_score / 10.0,
        )

    def _build_confidence_score(self, data: dict[str, Any]) -> ConfidenceScore:
        """Build ConfidenceScore from raw dict."""
        confidence_str = str(data.get("confidence", "medium")).lower()
        confidence = {
            "high": ConfidenceLevel.HIGH,
            "medium": ConfidenceLevel.MEDIUM,
            "low": ConfidenceLevel.LOW,
        }.get(confidence_str, ConfidenceLevel.MEDIUM)

        return ConfidenceScore(
            score=float(data.get("score", 5.0)),
            confidence=confidence,
            reasoning=data.get("reasoning"),
        )

    def _get_business_model_schema(self) -> dict[str, Any]:
        """Schema for business model analysis."""
        score_schema = {
            "type": "object",
            "properties": {
                "score": {"type": "number"},
                "confidence": {"type": "string"},
                "reasoning": {"type": "string"},
            },
        }
        return {
            "type": "object",
            "properties": {
                "overall_score": score_schema,
                "revenue_quality": score_schema,
                "margin_structure": score_schema,
                "scalability": score_schema,
                "defensibility": score_schema,
                "capital_efficiency": score_schema,
            },
        }

    def _get_market_schema(self) -> dict[str, Any]:
        """Schema for market analysis."""
        score_schema = {
            "type": "object",
            "properties": {
                "score": {"type": "number"},
                "confidence": {"type": "string"},
                "reasoning": {"type": "string"},
            },
        }
        return {
            "type": "object",
            "properties": {
                "market_score": score_schema,
                "tam_validity": score_schema,
                "market_timing": score_schema,
                "market_dynamics": {"type": "string"},
                "tailwinds": {"type": "array", "items": {"type": "string"}},
                "headwinds": {"type": "array", "items": {"type": "string"}},
            },
        }

    def _get_competitive_schema(self) -> dict[str, Any]:
        """Schema for competitive analysis."""
        score_schema = {
            "type": "object",
            "properties": {
                "score": {"type": "number"},
                "confidence": {"type": "string"},
                "reasoning": {"type": "string"},
            },
        }
        return {
            "type": "object",
            "properties": {
                "competitive_score": score_schema,
                "market_position": {"type": "string"},
                "differentiation_strength": score_schema,
                "barriers_to_entry": score_schema,
                "competitive_threats": {"type": "array", "items": {"type": "string"}},
                "sustainable_advantages": {"type": "array", "items": {"type": "string"}},
            },
        }

    def _get_growth_schema(self) -> dict[str, Any]:
        """Schema for growth analysis."""
        score_schema = {
            "type": "object",
            "properties": {
                "score": {"type": "number"},
                "confidence": {"type": "string"},
                "reasoning": {"type": "string"},
            },
        }
        return {
            "type": "object",
            "properties": {
                "growth_score": score_schema,
                "historical_growth_rate": {"type": "number"},
                "projected_growth_rate": {"type": "number"},
                "growth_drivers": {"type": "array", "items": {"type": "string"}},
                "growth_constraints": {"type": "array", "items": {"type": "string"}},
                "growth_sustainability": score_schema,
            },
        }

    def _get_thesis_schema(self) -> dict[str, Any]:
        """Schema for investment thesis."""
        return {
            "type": "object",
            "properties": {
                "investment_thesis": {
                    "type": "object",
                    "properties": {
                        "thesis_statement": {"type": "string"},
                        "key_beliefs": {"type": "array", "items": {"type": "string"}},
                        "upside_drivers": {"type": "array", "items": {"type": "string"}},
                        "key_concerns": {"type": "array", "items": {"type": "string"}},
                        "thesis_confidence": {"type": "string"},
                    },
                },
                "comparable_companies": {"type": "array"},
                "overall_attractiveness_score": {
                    "type": "object",
                    "properties": {
                        "score": {"type": "number"},
                        "confidence": {"type": "string"},
                        "reasoning": {"type": "string"},
                    },
                },
                "key_strengths": {"type": "array", "items": {"type": "string"}},
                "key_weaknesses": {"type": "array", "items": {"type": "string"}},
                "critical_questions": {"type": "array", "items": {"type": "string"}},
            },
        }
