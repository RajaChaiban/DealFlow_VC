"""
Valuation Agent for DealFlow AI Copilot.

Runs multiple valuation methodologies:
- Revenue multiple analysis (adjusted for growth, margins, quality)
- Stage-based benchmarking
- Simplified DCF projections
- Scenario analysis (bull/base/bear)
- Sensitivity analysis

Produces valuation range with key assumptions documented.
"""

from datetime import datetime
from typing import Any, Optional

from app.agents.base import BaseAgent
from app.models.schemas import (
    AnalysisResult,
    ComparableValuation,
    ConfidenceLevel,
    DCFValuation,
    ExtractionResult,
    MonetaryValue,
    RevenueMultipleValuation,
    SensitivityScenario,
    ValuationResult,
    ValuationScenario,
)
from app.utils.logger import logger

# Import prompts
import sys
sys.path.insert(0, ".")
from prompts.valuation_prompts import (
    COMPARABLE_ANALYSIS_PROMPT,
    DCF_VALUATION_PROMPT,
    REVENUE_MULTIPLE_PROMPT,
    SCENARIO_ANALYSIS_PROMPT,
    SENSITIVITY_ANALYSIS_PROMPT,
    VALUATION_SYNTHESIS_PROMPT,
    VALUATION_SYSTEM_PROMPT,
)


class ValuationAgent(BaseAgent[ValuationResult]):
    """
    Agent responsible for multi-methodology valuation analysis.

    Methodologies:
    - Revenue multiples (primary for early-stage)
    - Comparable company analysis
    - Simplified DCF

    Produces:
    - Valuation range (low/mid/high)
    - Scenario analysis
    - Sensitivity analysis
    - Comparison to company's ask

    Example:
        ```python
        agent = ValuationAgent()
        result = await agent.run(
            extraction_result=extraction_data,
            analysis_result=analysis_data
        )
        print(f"Valuation range: ${result.valuation_range_low.amount}M - ${result.valuation_range_high.amount}M")
        ```
    """

    @property
    def name(self) -> str:
        return "ValuationAgent"

    async def execute(
        self,
        extraction_result: ExtractionResult,
        analysis_result: Optional[AnalysisResult] = None,
    ) -> ValuationResult:
        """
        Execute multi-methodology valuation analysis.

        Args:
            extraction_result: Extracted data from pitch deck
            analysis_result: Optional analysis results for context

        Returns:
            ValuationResult with valuation range and scenarios

        Raises:
            AnalysisError: If valuation fails
        """
        logger.info(f"[{self.name}] Starting valuation for {extraction_result.company_name}")

        extraction_json = extraction_result.model_dump_json()
        analysis_json = analysis_result.model_dump_json() if analysis_result else "{}"

        # Step 1: Revenue multiple valuation
        logger.debug(f"[{self.name}] Running revenue multiple valuation...")
        revenue_multiple = await self._revenue_multiple_valuation(
            extraction_json, analysis_json
        )

        # Step 2: Comparable analysis
        logger.debug(f"[{self.name}] Running comparable analysis...")
        comparable = await self._comparable_valuation(extraction_json, analysis_json)

        # Step 3: DCF valuation (if enough data)
        logger.debug(f"[{self.name}] Running DCF valuation...")
        dcf = await self._dcf_valuation(extraction_json, analysis_json)

        # Step 4: Scenario analysis
        logger.debug(f"[{self.name}] Running scenario analysis...")
        scenarios = await self._scenario_analysis(
            extraction_json, revenue_multiple, comparable, dcf
        )

        # Step 5: Sensitivity analysis
        logger.debug(f"[{self.name}] Running sensitivity analysis...")
        sensitivity = self._sensitivity_analysis(revenue_multiple, extraction_result)

        # Step 6: Synthesize final valuation
        result = self._synthesize_valuation(
            extraction=extraction_result,
            revenue_multiple=revenue_multiple,
            comparable=comparable,
            dcf=dcf,
            scenarios=scenarios,
            sensitivity=sensitivity,
        )

        logger.info(
            f"[{self.name}] Valuation complete: "
            f"${result.valuation_range_low.amount:.1f}M - ${result.valuation_range_high.amount:.1f}M"
        )

        return result

    async def _revenue_multiple_valuation(
        self,
        extraction_json: str,
        analysis_json: str,
    ) -> RevenueMultipleValuation:
        """Calculate revenue multiple based valuation."""
        prompt = f"""{VALUATION_SYSTEM_PROMPT}

{REVENUE_MULTIPLE_PROMPT.format(financial_data=extraction_json, analysis_data=analysis_json)}"""

        response = await self.client.generate_structured(
            prompt=prompt,
            response_schema=self._get_revenue_multiple_schema(),
            model="pro",
            temperature=0.2,
        )

        # Build MonetaryValue objects
        base_revenue = response.get("base_revenue", {})
        implied_val = response.get("implied_valuation", {})

        return RevenueMultipleValuation(
            methodology="Revenue Multiple",
            base_revenue=MonetaryValue(
                amount=float(base_revenue.get("amount", 0)),
                currency=base_revenue.get("currency", "USD"),
                unit=base_revenue.get("unit", "M"),
            ),
            comparable_multiple_range=tuple(
                response.get("comparable_multiple_range", [5.0, 15.0])[:2]
            ),
            applied_multiple=float(response.get("applied_multiple", 10.0)),
            multiple_adjustments=response.get("multiple_adjustments", {}),
            implied_valuation=MonetaryValue(
                amount=float(implied_val.get("amount", 0)),
                currency=implied_val.get("currency", "USD"),
                unit=implied_val.get("unit", "M"),
            ),
            reasoning=response.get("reasoning", ""),
        )

    async def _comparable_valuation(
        self,
        extraction_json: str,
        analysis_json: str,
    ) -> ComparableValuation:
        """Perform comparable company analysis."""
        prompt = f"""{VALUATION_SYSTEM_PROMPT}

{COMPARABLE_ANALYSIS_PROMPT.format(company_data=extraction_json, analysis_data=analysis_json)}"""

        response = await self.client.generate_structured(
            prompt=prompt,
            response_schema=self._get_comparable_schema(),
            model="pro",
            temperature=0.3,
        )

        # Build valuation range
        val_range = response.get("implied_valuation_range", {})
        low_val = val_range.get("low", {})
        high_val = val_range.get("high", {})

        return ComparableValuation(
            methodology="Comparable Analysis",
            comparables_used=[c.get("name", "") for c in response.get("comparables_used", [])],
            median_multiple=float(response.get("median_multiple", 10.0)),
            implied_valuation_range=(
                MonetaryValue(
                    amount=float(low_val.get("amount", 0)),
                    unit=low_val.get("unit", "M"),
                ),
                MonetaryValue(
                    amount=float(high_val.get("amount", 0)),
                    unit=high_val.get("unit", "M"),
                ),
            ),
            adjustments_made=response.get("adjustments_made", []),
        )

    async def _dcf_valuation(
        self,
        extraction_json: str,
        analysis_json: str,
    ) -> DCFValuation:
        """Perform simplified DCF valuation."""
        prompt = f"""{VALUATION_SYSTEM_PROMPT}

{DCF_VALUATION_PROMPT.format(financial_data=extraction_json, analysis_data=analysis_json)}"""

        response = await self.client.generate_structured(
            prompt=prompt,
            response_schema=self._get_dcf_schema(),
            model="pro",
            temperature=0.2,
        )

        terminal = response.get("terminal_value", {})
        key_assumptions = response.get("key_assumptions", {})

        return DCFValuation(
            methodology="Discounted Cash Flow",
            projection_years=response.get("projection_years", 5),
            revenue_cagr_assumption=float(key_assumptions.get("revenue_cagr", 0.3)),
            terminal_growth_rate=float(terminal.get("terminal_growth_rate", 0.03)),
            discount_rate=float(response.get("discount_rate", 0.35)),
            terminal_value=MonetaryValue(
                amount=float(terminal.get("terminal_value", {}).get("amount", 0)),
                unit=terminal.get("terminal_value", {}).get("unit", "M"),
            ),
            enterprise_value=MonetaryValue(
                amount=float(response.get("enterprise_value", {}).get("amount", 0)),
                unit=response.get("enterprise_value", {}).get("unit", "M"),
            ),
            key_assumptions=key_assumptions,
        )

    async def _scenario_analysis(
        self,
        extraction_json: str,
        revenue_multiple: RevenueMultipleValuation,
        comparable: ComparableValuation,
        dcf: DCFValuation,
    ) -> list[ValuationScenario]:
        """Generate bull/base/bear scenarios."""
        # Calculate base valuation from methodologies
        valuations = [
            revenue_multiple.implied_valuation.amount,
            (comparable.implied_valuation_range[0].amount + comparable.implied_valuation_range[1].amount) / 2,
            dcf.enterprise_value.amount,
        ]
        valid_valuations = [v for v in valuations if v > 0]
        base_value = sum(valid_valuations) / len(valid_valuations) if valid_valuations else 50.0

        # Generate scenarios
        scenarios = [
            ValuationScenario(
                scenario_name="Bull",
                probability=0.2,
                valuation=MonetaryValue(amount=base_value * 1.5, unit="M"),
                key_assumptions=[
                    "Growth exceeds projections by 20%+",
                    "Multiple expansion due to market leadership",
                    "Successful expansion into adjacent markets",
                ],
                implied_multiple=revenue_multiple.applied_multiple * 1.3,
            ),
            ValuationScenario(
                scenario_name="Base",
                probability=0.6,
                valuation=MonetaryValue(amount=base_value, unit="M"),
                key_assumptions=[
                    "Growth meets current trajectory",
                    "Margins improve as expected",
                    "Market conditions remain stable",
                ],
                implied_multiple=revenue_multiple.applied_multiple,
            ),
            ValuationScenario(
                scenario_name="Bear",
                probability=0.2,
                valuation=MonetaryValue(amount=base_value * 0.6, unit="M"),
                key_assumptions=[
                    "Growth slows significantly",
                    "Competitive pressure increases",
                    "Multiple compression in risk-off environment",
                ],
                implied_multiple=revenue_multiple.applied_multiple * 0.6,
            ),
        ]

        return scenarios

    def _sensitivity_analysis(
        self,
        revenue_multiple: RevenueMultipleValuation,
        extraction: ExtractionResult,
    ) -> list[SensitivityScenario]:
        """Generate sensitivity analysis."""
        scenarios: list[SensitivityScenario] = []
        base_valuation = revenue_multiple.implied_valuation.amount

        # Revenue growth sensitivity
        if extraction.financials.revenue_growth_rate:
            base_growth = extraction.financials.revenue_growth_rate
            for change in [-0.2, 0.2]:
                new_growth = base_growth + change
                # Higher growth typically commands higher multiple
                multiple_change = change * 2  # 2x leverage on multiple
                new_val = base_valuation * (1 + multiple_change)

                scenarios.append(
                    SensitivityScenario(
                        variable_name="Revenue Growth Rate",
                        base_value=base_growth,
                        adjusted_value=new_growth,
                        resulting_valuation=MonetaryValue(amount=new_val, unit="M"),
                        change_percentage=(new_val - base_valuation) / base_valuation,
                    )
                )

        # Multiple sensitivity
        base_multiple = revenue_multiple.applied_multiple
        for change in [-2.0, 2.0]:
            new_multiple = base_multiple + change
            new_val = base_valuation * (new_multiple / base_multiple)

            scenarios.append(
                SensitivityScenario(
                    variable_name="Valuation Multiple",
                    base_value=base_multiple,
                    adjusted_value=new_multiple,
                    resulting_valuation=MonetaryValue(amount=new_val, unit="M"),
                    change_percentage=(new_val - base_valuation) / base_valuation,
                )
            )

        # Margin sensitivity
        if extraction.financials.gross_margin:
            base_margin = extraction.financials.gross_margin
            for change in [-0.05, 0.05]:
                new_margin = base_margin + change
                # Margin impacts quality perception
                val_change = change * 5  # 5x leverage
                new_val = base_valuation * (1 + val_change)

                scenarios.append(
                    SensitivityScenario(
                        variable_name="Gross Margin",
                        base_value=base_margin,
                        adjusted_value=new_margin,
                        resulting_valuation=MonetaryValue(amount=new_val, unit="M"),
                        change_percentage=(new_val - base_valuation) / base_valuation,
                    )
                )

        return scenarios

    def _synthesize_valuation(
        self,
        extraction: ExtractionResult,
        revenue_multiple: RevenueMultipleValuation,
        comparable: ComparableValuation,
        dcf: DCFValuation,
        scenarios: list[ValuationScenario],
        sensitivity: list[SensitivityScenario],
    ) -> ValuationResult:
        """Synthesize all valuation work into final result."""
        # Collect all valuations
        all_values = [
            revenue_multiple.implied_valuation.amount,
            comparable.implied_valuation_range[0].amount,
            comparable.implied_valuation_range[1].amount,
            dcf.enterprise_value.amount,
        ]
        valid_values = [v for v in all_values if v > 0]

        if not valid_values:
            # Fallback if no valid valuations
            valid_values = [50.0]

        # Calculate range
        low = min(valid_values)
        high = max(valid_values)
        mid = sum(valid_values) / len(valid_values)

        # Probability weighted (from scenarios)
        prob_weighted = sum(
            s.valuation.amount * s.probability for s in scenarios
        )

        # Compare to ask
        ask_comparison = ""
        discount_premium = 0.0

        if extraction.funding_ask:
            ask = extraction.funding_ask.normalized_amount
            if extraction.financials.pre_money_valuation:
                ask_val = extraction.financials.pre_money_valuation.normalized_amount
                discount_premium = (mid - ask_val) / ask_val if ask_val > 0 else 0

                if discount_premium > 0.2:
                    ask_comparison = f"Company's ask of ${ask_val/1e6:.0f}M is below our valuation range (attractive)"
                elif discount_premium < -0.2:
                    ask_comparison = f"Company's ask of ${ask_val/1e6:.0f}M is above our valuation range (expensive)"
                else:
                    ask_comparison = f"Company's ask of ${ask_val/1e6:.0f}M is within our valuation range (fair)"

        # Determine confidence
        confidence = ConfidenceLevel.MEDIUM
        if len(valid_values) >= 3 and (high - low) / mid < 0.5:
            confidence = ConfidenceLevel.HIGH
        elif len(valid_values) < 2 or (high - low) / mid > 1.0:
            confidence = ConfidenceLevel.LOW

        # Calculate target returns
        target_return = 3.0  # 3x for early stage
        if extraction.stage:
            stage_returns = {
                "pre_seed": 10.0,
                "seed": 7.0,
                "series_a": 5.0,
                "series_b": 3.5,
                "series_c": 2.5,
                "growth": 2.0,
                "late_stage": 1.5,
            }
            target_return = stage_returns.get(extraction.stage.value, 3.0)

        # Key valuation risks
        risks: list[str] = []
        if (high - low) / mid > 0.5:
            risks.append("Wide valuation range indicates high uncertainty")
        if not extraction.financials.revenue:
            risks.append("No revenue data - valuation highly speculative")
        if discount_premium < -0.3:
            risks.append("Company's valuation expectations may be too high")

        methodologies_used = ["Revenue Multiple"]
        if comparable.comparables_used:
            methodologies_used.append("Comparable Analysis")
        if dcf.enterprise_value.amount > 0:
            methodologies_used.append("DCF")

        return ValuationResult(
            revenue_multiple=revenue_multiple,
            comparable_analysis=comparable,
            dcf=dcf,
            scenarios=scenarios,
            valuation_range_low=MonetaryValue(amount=low, unit="M"),
            valuation_range_mid=MonetaryValue(amount=mid, unit="M"),
            valuation_range_high=MonetaryValue(amount=high, unit="M"),
            probability_weighted_value=MonetaryValue(amount=prob_weighted, unit="M"),
            sensitivity_analysis=sensitivity,
            ask_vs_valuation=ask_comparison,
            implied_discount_premium=discount_premium,
            target_return_multiple=target_return,
            target_irr=0.30,  # 30% IRR target
            valuation_confidence=confidence,
            key_valuation_risks=risks,
            methodologies_used=methodologies_used,
            assessment_date=datetime.utcnow(),
        )

    def _get_revenue_multiple_schema(self) -> dict[str, Any]:
        """Schema for revenue multiple response."""
        return {
            "type": "object",
            "properties": {
                "base_revenue": {
                    "type": "object",
                    "properties": {
                        "amount": {"type": "number"},
                        "currency": {"type": "string"},
                        "unit": {"type": "string"},
                        "type": {"type": "string"},
                    },
                },
                "comparable_multiple_range": {
                    "type": "array",
                    "items": {"type": "number"},
                },
                "applied_multiple": {"type": "number"},
                "multiple_adjustments": {"type": "object"},
                "implied_valuation": {
                    "type": "object",
                    "properties": {
                        "amount": {"type": "number"},
                        "currency": {"type": "string"},
                        "unit": {"type": "string"},
                    },
                },
                "reasoning": {"type": "string"},
            },
        }

    def _get_comparable_schema(self) -> dict[str, Any]:
        """Schema for comparable analysis response."""
        return {
            "type": "object",
            "properties": {
                "comparables_used": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "transaction_type": {"type": "string"},
                            "valuation": {"type": "object"},
                            "implied_multiple": {"type": "number"},
                        },
                    },
                },
                "median_multiple": {"type": "number"},
                "implied_valuation_range": {
                    "type": "object",
                    "properties": {
                        "low": {"type": "object"},
                        "high": {"type": "object"},
                    },
                },
                "adjustments_made": {"type": "array", "items": {"type": "string"}},
            },
        }

    def _get_dcf_schema(self) -> dict[str, Any]:
        """Schema for DCF response."""
        return {
            "type": "object",
            "properties": {
                "projection_years": {"type": "integer"},
                "projections": {"type": "array"},
                "terminal_value": {
                    "type": "object",
                    "properties": {
                        "terminal_growth_rate": {"type": "number"},
                        "terminal_value": {"type": "object"},
                    },
                },
                "discount_rate": {"type": "number"},
                "enterprise_value": {"type": "object"},
                "key_assumptions": {"type": "object"},
            },
        }
