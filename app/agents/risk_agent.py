"""
Risk Agent for DealFlow AI Copilot.

Systematically identifies red flags across:
- Financial risks (burn rate, unit economics, projections)
- Team risks (background, gaps, key person dependency)
- Market risks (competition, timing, regulatory)
- Operational risks (execution, technology, legal)
- Data consistency (cross-checking numbers for contradictions)

Prioritizes risks by severity and generates risk-adjusted recommendations.
"""

import uuid
from typing import Any, Optional

from app.agents.base import BaseAgent
from app.models.schemas import (
    ConfidenceLevel,
    DataConsistencyCheck,
    ExtractionResult,
    RecommendationType,
    RiskCategory,
    RiskItem,
    RiskResult,
    RiskSeverity,
    RiskSummary,
)
from app.utils.logger import logger

# Import prompts
import sys
sys.path.insert(0, ".")
from prompts.risk_prompts import (
    DATA_CONSISTENCY_PROMPT,
    FINANCIAL_RISK_PROMPT,
    MARKET_RISK_PROMPT,
    OPERATIONAL_RISK_PROMPT,
    RISK_SYNTHESIS_PROMPT,
    RISK_SYSTEM_PROMPT,
    TEAM_RISK_PROMPT,
)


class RiskAgent(BaseAgent[RiskResult]):
    """
    Agent responsible for comprehensive risk assessment.

    Identifies risks across multiple categories:
    - Financial: burn rate, unit economics, projections
    - Team: backgrounds, gaps, dependencies
    - Market: competition, timing, regulatory
    - Operational: execution, technology, legal
    - Consistency: data validation and cross-checks

    Example:
        ```python
        agent = RiskAgent()
        result = await agent.run(extraction_result=extraction_data)
        print(f"Overall risk score: {result.overall_risk_score}/10")
        print(f"Critical risks: {result.critical_risks}")
        print(f"Recommendation: {result.risk_adjusted_recommendation}")
        ```
    """

    @property
    def name(self) -> str:
        return "RiskAgent"

    async def execute(
        self,
        extraction_result: ExtractionResult,
    ) -> RiskResult:
        """
        Execute comprehensive risk assessment.

        Args:
            extraction_result: Extracted data from pitch deck

        Returns:
            RiskResult with all identified risks and recommendations

        Raises:
            AnalysisError: If risk assessment fails
        """
        logger.info(f"[{self.name}] Starting risk assessment for {extraction_result.company_name}")

        # Step 1: Identify financial risks
        logger.debug(f"[{self.name}] Assessing financial risks...")
        financial_risks = await self._assess_financial_risks(extraction_result)

        # Step 2: Identify team risks
        logger.debug(f"[{self.name}] Assessing team risks...")
        team_risks = await self._assess_team_risks(extraction_result)

        # Step 3: Identify market risks
        logger.debug(f"[{self.name}] Assessing market risks...")
        market_risks = await self._assess_market_risks(extraction_result)

        # Step 4: Identify operational risks
        logger.debug(f"[{self.name}] Assessing operational risks...")
        operational_risks = await self._assess_operational_risks(extraction_result)

        # Step 5: Data consistency checks
        logger.debug(f"[{self.name}] Running data consistency checks...")
        consistency_results = await self._check_data_consistency(extraction_result)

        # Step 6: Synthesize all risks
        all_risks = financial_risks + team_risks + market_risks + operational_risks
        logger.debug(f"[{self.name}] Synthesizing {len(all_risks)} risks...")

        result = await self._synthesize_risks(
            all_risks=all_risks,
            consistency_results=consistency_results,
        )

        logger.info(
            f"[{self.name}] Risk assessment complete: "
            f"Score {result.overall_risk_score}/10, "
            f"{result.total_risks} total risks, "
            f"{result.critical_risks} critical"
        )

        return result

    async def _assess_financial_risks(
        self,
        extraction: ExtractionResult,
    ) -> list[RiskItem]:
        """Assess financial risks."""
        financial_json = extraction.financials.model_dump_json()
        unit_econ_json = extraction.unit_economics.model_dump_json()

        prompt = f"""{RISK_SYSTEM_PROMPT}

{FINANCIAL_RISK_PROMPT.format(financial_data=f"Financials: {financial_json}\n\nUnit Economics: {unit_econ_json}")}"""

        response = await self.client.generate_structured(
            prompt=prompt,
            response_schema=self._get_risk_array_schema(),
            model="pro",
            temperature=0.2,
        )

        risks = self._parse_risks(response, RiskCategory.FINANCIAL)

        # Add programmatic checks
        risks.extend(self._check_financial_red_flags(extraction))

        return risks

    async def _assess_team_risks(
        self,
        extraction: ExtractionResult,
    ) -> list[RiskItem]:
        """Assess team-related risks."""
        team_json = extraction.team.model_dump_json()

        prompt = f"""{RISK_SYSTEM_PROMPT}

{TEAM_RISK_PROMPT.format(team_data=team_json)}"""

        response = await self.client.generate_structured(
            prompt=prompt,
            response_schema=self._get_risk_array_schema(),
            model="pro",
            temperature=0.2,
        )

        risks = self._parse_risks(response, RiskCategory.TEAM)

        # Add programmatic checks
        risks.extend(self._check_team_red_flags(extraction))

        return risks

    async def _assess_market_risks(
        self,
        extraction: ExtractionResult,
    ) -> list[RiskItem]:
        """Assess market-related risks."""
        market_json = extraction.market.model_dump_json()
        competitive_json = str([c.model_dump() for c in extraction.competitors])

        prompt = f"""{RISK_SYSTEM_PROMPT}

{MARKET_RISK_PROMPT.format(market_data=market_json, competitive_data=competitive_json)}"""

        response = await self.client.generate_structured(
            prompt=prompt,
            response_schema=self._get_risk_array_schema(),
            model="pro",
            temperature=0.2,
        )

        return self._parse_risks(response, RiskCategory.MARKET)

    async def _assess_operational_risks(
        self,
        extraction: ExtractionResult,
    ) -> list[RiskItem]:
        """Assess operational risks."""
        company_json = extraction.model_dump_json()

        prompt = f"""{RISK_SYSTEM_PROMPT}

{OPERATIONAL_RISK_PROMPT.format(company_data=company_json[:30000])}"""

        response = await self.client.generate_structured(
            prompt=prompt,
            response_schema=self._get_risk_array_schema(),
            model="pro",
            temperature=0.2,
        )

        return self._parse_risks(response, RiskCategory.OPERATIONAL)

    async def _check_data_consistency(
        self,
        extraction: ExtractionResult,
    ) -> list[DataConsistencyCheck]:
        """Run data consistency checks."""
        checks: list[DataConsistencyCheck] = []

        # Check 1: MRR × 12 = ARR
        if extraction.financials.mrr and extraction.financials.arr:
            mrr = extraction.financials.mrr.normalized_amount
            arr = extraction.financials.arr.normalized_amount
            expected_arr = mrr * 12
            passed = abs(expected_arr - arr) / max(arr, 1) < 0.1

            checks.append(
                DataConsistencyCheck(
                    check_name="MRR × 12 = ARR",
                    passed=passed,
                    discrepancy=None if passed else f"MRR×12=${expected_arr:,.0f}, ARR=${arr:,.0f}",
                    values_compared={"mrr_x_12": expected_arr, "stated_arr": arr},
                )
            )

        # Check 2: Burn rate × runway = cash
        if (
            extraction.financials.monthly_burn_rate
            and extraction.financials.runway_months
            and extraction.financials.cash_on_hand
        ):
            burn = extraction.financials.monthly_burn_rate.normalized_amount
            runway = extraction.financials.runway_months
            cash = extraction.financials.cash_on_hand.normalized_amount
            expected_cash = burn * runway
            passed = abs(expected_cash - cash) / max(cash, 1) < 0.2

            checks.append(
                DataConsistencyCheck(
                    check_name="Burn × Runway = Cash",
                    passed=passed,
                    discrepancy=None if passed else f"Burn×Runway=${expected_cash:,.0f}, Cash=${cash:,.0f}",
                    values_compared={"burn_x_runway": expected_cash, "stated_cash": cash},
                )
            )

        # Check 3: LTV/CAC ratio consistency
        if (
            extraction.unit_economics.ltv
            and extraction.unit_economics.cac
            and extraction.unit_economics.ltv_cac_ratio
        ):
            ltv = extraction.unit_economics.ltv.normalized_amount
            cac = extraction.unit_economics.cac.normalized_amount
            calculated_ratio = ltv / cac if cac > 0 else 0
            stated_ratio = extraction.unit_economics.ltv_cac_ratio
            passed = abs(calculated_ratio - stated_ratio) / max(stated_ratio, 0.1) < 0.15

            checks.append(
                DataConsistencyCheck(
                    check_name="LTV/CAC Calculation",
                    passed=passed,
                    discrepancy=None if passed else f"Calculated={calculated_ratio:.2f}x, Stated={stated_ratio:.2f}x",
                    values_compared={"calculated": calculated_ratio, "stated": stated_ratio},
                )
            )

        # Check 4: Revenue growth consistency with historical data
        if (
            extraction.financials.revenue_history
            and len(extraction.financials.revenue_history) >= 2
            and extraction.financials.revenue_growth_rate
        ):
            history = extraction.financials.revenue_history
            # Calculate growth from history
            try:
                recent = float(history[-1].get("revenue", 0))
                previous = float(history[-2].get("revenue", 0))
                if previous > 0:
                    calculated_growth = (recent - previous) / previous
                    stated_growth = extraction.financials.revenue_growth_rate
                    passed = abs(calculated_growth - stated_growth) < 0.2

                    checks.append(
                        DataConsistencyCheck(
                            check_name="Revenue Growth Consistency",
                            passed=passed,
                            discrepancy=None if passed else f"Historical={calculated_growth:.1%}, Stated={stated_growth:.1%}",
                            values_compared={"historical": calculated_growth, "stated": stated_growth},
                        )
                    )
            except (KeyError, ValueError, TypeError):
                pass

        return checks

    def _check_financial_red_flags(
        self,
        extraction: ExtractionResult,
    ) -> list[RiskItem]:
        """Programmatically check for financial red flags."""
        risks: list[RiskItem] = []
        fin = extraction.financials
        ue = extraction.unit_economics

        # Low runway
        if fin.runway_months and fin.runway_months < 6:
            risks.append(
                RiskItem(
                    id=f"FIN-{uuid.uuid4().hex[:6]}",
                    title="Critical Runway Shortage",
                    description=f"Company has only {fin.runway_months} months of runway remaining",
                    category=RiskCategory.FINANCIAL,
                    severity=RiskSeverity.CRITICAL,
                    likelihood=ConfidenceLevel.HIGH,
                    impact="Company may run out of cash before achieving key milestones",
                    mitigation="Requires immediate funding or cost reduction",
                    evidence=[f"{fin.runway_months} months runway"],
                    affected_areas=["Cash", "Operations", "Growth"],
                )
            )

        # Negative unit economics
        if ue.ltv_cac_ratio and ue.ltv_cac_ratio < 1.0:
            risks.append(
                RiskItem(
                    id=f"FIN-{uuid.uuid4().hex[:6]}",
                    title="Negative Unit Economics",
                    description=f"LTV/CAC ratio of {ue.ltv_cac_ratio:.2f}x indicates unprofitable customer acquisition",
                    category=RiskCategory.FINANCIAL,
                    severity=RiskSeverity.CRITICAL,
                    likelihood=ConfidenceLevel.HIGH,
                    impact="Each new customer loses money; growth accelerates losses",
                    mitigation="Must improve retention, pricing, or reduce CAC",
                    evidence=[f"LTV/CAC = {ue.ltv_cac_ratio:.2f}x"],
                    affected_areas=["Profitability", "Scalability", "Sustainability"],
                )
            )

        # High burn rate relative to revenue
        if fin.monthly_burn_rate and fin.revenue:
            burn = fin.monthly_burn_rate.normalized_amount
            monthly_rev = fin.revenue.normalized_amount / 12
            if burn > monthly_rev * 3:
                risks.append(
                    RiskItem(
                        id=f"FIN-{uuid.uuid4().hex[:6]}",
                        title="Excessive Burn Rate",
                        description=f"Monthly burn (${burn:,.0f}) is {burn/max(monthly_rev,1):.1f}x monthly revenue",
                        category=RiskCategory.FINANCIAL,
                        severity=RiskSeverity.HIGH,
                        likelihood=ConfidenceLevel.MEDIUM,
                        impact="High capital requirements, dilution risk",
                        mitigation="Reduce expenses or accelerate revenue growth",
                        evidence=[f"Burn/Revenue = {burn/max(monthly_rev,1):.1f}x"],
                        affected_areas=["Capital Efficiency", "Runway", "Returns"],
                    )
                )

        # High churn
        if ue.churn_rate and ue.churn_rate > 0.05:
            risks.append(
                RiskItem(
                    id=f"FIN-{uuid.uuid4().hex[:6]}",
                    title="High Customer Churn",
                    description=f"Monthly churn of {ue.churn_rate:.1%} indicates retention issues",
                    category=RiskCategory.FINANCIAL,
                    severity=RiskSeverity.HIGH,
                    likelihood=ConfidenceLevel.HIGH,
                    impact="Reduces LTV, increases CAC payback, threatens growth",
                    mitigation="Focus on product-market fit and customer success",
                    evidence=[f"Monthly churn = {ue.churn_rate:.1%}"],
                    affected_areas=["Revenue", "Unit Economics", "Growth"],
                )
            )

        return risks

    def _check_team_red_flags(
        self,
        extraction: ExtractionResult,
    ) -> list[RiskItem]:
        """Programmatically check for team red flags."""
        risks: list[RiskItem] = []
        team = extraction.team

        # Solo founder
        if len(team.founders) == 1:
            risks.append(
                RiskItem(
                    id=f"TEAM-{uuid.uuid4().hex[:6]}",
                    title="Solo Founder Risk",
                    description="Single founder increases key person dependency",
                    category=RiskCategory.TEAM,
                    severity=RiskSeverity.MEDIUM,
                    likelihood=ConfidenceLevel.MEDIUM,
                    impact="Higher risk of burnout, limited skill coverage",
                    mitigation="Identify co-founder or strong leadership team",
                    evidence=["1 founder"],
                    affected_areas=["Leadership", "Execution", "Resilience"],
                )
            )

        # No founders listed
        if len(team.founders) == 0:
            risks.append(
                RiskItem(
                    id=f"TEAM-{uuid.uuid4().hex[:6]}",
                    title="Unknown Founding Team",
                    description="No founder information provided in pitch deck",
                    category=RiskCategory.TEAM,
                    severity=RiskSeverity.HIGH,
                    likelihood=ConfidenceLevel.HIGH,
                    impact="Cannot assess team quality or experience",
                    mitigation="Request detailed team backgrounds",
                    evidence=["No founder data"],
                    affected_areas=["Due Diligence", "Team Assessment"],
                )
            )

        # Significant team gaps
        if len(team.team_gaps) >= 2:
            risks.append(
                RiskItem(
                    id=f"TEAM-{uuid.uuid4().hex[:6]}",
                    title="Multiple Team Gaps",
                    description=f"Identified gaps: {', '.join(team.team_gaps[:3])}",
                    category=RiskCategory.TEAM,
                    severity=RiskSeverity.MEDIUM,
                    likelihood=ConfidenceLevel.MEDIUM,
                    impact="May struggle to execute on key initiatives",
                    mitigation="Develop hiring plan for critical roles",
                    evidence=team.team_gaps,
                    affected_areas=["Execution", "Growth", "Product"],
                )
            )

        return risks

    def _parse_risks(
        self,
        response: Any,
        default_category: RiskCategory,
    ) -> list[RiskItem]:
        """Parse risk items from LLM response."""
        risks: list[RiskItem] = []

        # Handle both array and object responses
        risk_list = response if isinstance(response, list) else response.get("risks", [])

        for risk_data in risk_list:
            if not isinstance(risk_data, dict):
                continue

            # Map severity
            severity_str = risk_data.get("severity", "medium").lower()
            severity = {
                "critical": RiskSeverity.CRITICAL,
                "high": RiskSeverity.HIGH,
                "medium": RiskSeverity.MEDIUM,
                "low": RiskSeverity.LOW,
            }.get(severity_str, RiskSeverity.MEDIUM)

            # Map likelihood
            likelihood_str = risk_data.get("likelihood", "medium").lower()
            likelihood = {
                "high": ConfidenceLevel.HIGH,
                "medium": ConfidenceLevel.MEDIUM,
                "low": ConfidenceLevel.LOW,
            }.get(likelihood_str, ConfidenceLevel.MEDIUM)

            # Map category
            category_str = risk_data.get("category", "").lower()
            category = {
                "financial": RiskCategory.FINANCIAL,
                "team": RiskCategory.TEAM,
                "market": RiskCategory.MARKET,
                "product": RiskCategory.PRODUCT,
                "legal": RiskCategory.LEGAL,
                "operational": RiskCategory.OPERATIONAL,
                "consistency": RiskCategory.CONSISTENCY,
            }.get(category_str, default_category)

            risks.append(
                RiskItem(
                    id=risk_data.get("id", f"{category.value[:3].upper()}-{uuid.uuid4().hex[:6]}"),
                    title=risk_data.get("title", "Unnamed Risk"),
                    description=risk_data.get("description", ""),
                    category=category,
                    severity=severity,
                    likelihood=likelihood,
                    impact=risk_data.get("impact", ""),
                    mitigation=risk_data.get("mitigation"),
                    evidence=risk_data.get("evidence", []),
                    affected_areas=risk_data.get("affected_areas", []),
                )
            )

        return risks

    async def _synthesize_risks(
        self,
        all_risks: list[RiskItem],
        consistency_results: list[DataConsistencyCheck],
    ) -> RiskResult:
        """Synthesize all risks into final result."""
        # Count by severity
        critical_count = sum(1 for r in all_risks if r.severity == RiskSeverity.CRITICAL)
        high_count = sum(1 for r in all_risks if r.severity == RiskSeverity.HIGH)
        medium_count = sum(1 for r in all_risks if r.severity == RiskSeverity.MEDIUM)
        low_count = sum(1 for r in all_risks if r.severity == RiskSeverity.LOW)

        # Build summaries by category
        categories = set(r.category for r in all_risks)
        summaries: list[RiskSummary] = []

        for category in categories:
            cat_risks = [r for r in all_risks if r.category == category]
            summaries.append(
                RiskSummary(
                    category=category,
                    risk_count=len(cat_risks),
                    critical_count=sum(1 for r in cat_risks if r.severity == RiskSeverity.CRITICAL),
                    high_count=sum(1 for r in cat_risks if r.severity == RiskSeverity.HIGH),
                    medium_count=sum(1 for r in cat_risks if r.severity == RiskSeverity.MEDIUM),
                    low_count=sum(1 for r in cat_risks if r.severity == RiskSeverity.LOW),
                    top_risks=[r.title for r in cat_risks[:3]],
                )
            )

        # Calculate data integrity score
        passed_checks = sum(1 for c in consistency_results if c.passed)
        data_integrity = passed_checks / len(consistency_results) if consistency_results else 0.8

        # Calculate overall risk score (0-10, higher = more risky)
        risk_score = min(10.0, (critical_count * 3) + (high_count * 1.5) + (medium_count * 0.5))

        # Determine recommendation
        if critical_count >= 2 or risk_score >= 8:
            recommendation = RecommendationType.STRONG_PASS
            reasoning = f"Multiple critical risks ({critical_count}) make this investment too risky"
        elif critical_count == 1 or risk_score >= 6:
            recommendation = RecommendationType.PASS
            reasoning = f"Significant risks (score {risk_score:.1f}/10) outweigh potential upside"
        elif high_count >= 3 or risk_score >= 4:
            recommendation = RecommendationType.MORE_DILIGENCE
            reasoning = f"Several high risks require deeper investigation before deciding"
        elif risk_score >= 2:
            recommendation = RecommendationType.CONDITIONAL_INVEST
            reasoning = f"Acceptable risk profile if key concerns can be addressed"
        else:
            recommendation = RecommendationType.INVEST
            reasoning = f"Risk profile (score {risk_score:.1f}/10) is acceptable"

        # Identify deal breakers
        deal_breakers = [
            r.title for r in all_risks
            if r.severity == RiskSeverity.CRITICAL
        ]

        # Must verify items
        must_verify = [
            r.title for r in all_risks
            if r.severity in [RiskSeverity.CRITICAL, RiskSeverity.HIGH]
        ][:5]

        return RiskResult(
            risks=all_risks,
            risk_summaries=summaries,
            consistency_checks=consistency_results,
            data_integrity_score=data_integrity,
            overall_risk_score=risk_score,
            risk_adjusted_recommendation=recommendation,
            recommendation_reasoning=reasoning,
            deal_breakers=deal_breakers,
            must_verify_items=must_verify,
            total_risks=len(all_risks),
            critical_risks=critical_count,
            high_risks=high_count,
            assessment_confidence=0.8 if len(all_risks) > 5 else 0.6,
        )

    def _get_risk_array_schema(self) -> dict[str, Any]:
        """Schema for risk array response."""
        return {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "category": {"type": "string"},
                    "severity": {"type": "string"},
                    "likelihood": {"type": "string"},
                    "impact": {"type": "string"},
                    "mitigation": {"type": ["string", "null"]},
                    "evidence": {"type": "array", "items": {"type": "string"}},
                    "affected_areas": {"type": "array", "items": {"type": "string"}},
                },
            },
        }
