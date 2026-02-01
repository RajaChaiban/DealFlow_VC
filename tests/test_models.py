"""
Tests for Pydantic models and schemas.

Tests cover:
- ExtractionResult validation (required fields, defaults, optional fields)
- ICMemo creation (full model assembly)
- MonetaryValue.normalized_amount (unit multiplier logic)
- Enum validation
- Nested model construction

Run with: pytest tests/test_models.py -v
"""

from datetime import datetime
from typing import Any

import pytest
from pydantic import ValidationError

from app.models.schemas import (
    AgentStatus,
    AnalysisResult,
    BusinessModelScore,
    CompetitiveAnalysis,
    ConfidenceLevel,
    ConfidenceScore,
    DealStage,
    ExecutiveSummary,
    ExtractionResult,
    FinancialMetrics,
    FounderInfo,
    GrowthAnalysis,
    ICMemo,
    InvestmentThesis,
    MarketAnalysis,
    MonetaryValue,
    RecommendationType,
    RiskCategory,
    RiskItem,
    RiskResult,
    RiskSeverity,
    RiskSummary,
    TeamInfo,
    TractionMetrics,
    UnitEconomics,
    ValuationResult,
    ValuationScenario,
)


# ---------------------------------------------------------------------------
# MonetaryValue Tests
# ---------------------------------------------------------------------------

class TestMonetaryValue:
    """Tests for the MonetaryValue model and its normalized_amount property."""

    def test_basic_creation(self) -> None:
        """MonetaryValue should be created with amount and defaults."""
        mv = MonetaryValue(amount=100.0)
        assert mv.amount == 100.0
        assert mv.currency == "USD"
        assert mv.unit == ""

    def test_normalized_amount_no_unit(self) -> None:
        """With no unit, normalized_amount should equal the raw amount."""
        mv = MonetaryValue(amount=5000.0)
        assert mv.normalized_amount == 5000.0

    def test_normalized_amount_thousands(self) -> None:
        """Unit 'K' should multiply amount by 1,000."""
        mv = MonetaryValue(amount=250.0, unit="K")
        assert mv.normalized_amount == 250_000.0

    def test_normalized_amount_millions(self) -> None:
        """Unit 'M' should multiply amount by 1,000,000."""
        mv = MonetaryValue(amount=3.2, unit="M")
        assert mv.normalized_amount == 3_200_000.0

    def test_normalized_amount_billions(self) -> None:
        """Unit 'B' should multiply amount by 1,000,000,000."""
        mv = MonetaryValue(amount=1.5, unit="B")
        assert mv.normalized_amount == 1_500_000_000.0

    def test_normalized_amount_case_insensitive(self) -> None:
        """Unit lookup should be case-insensitive."""
        mv_lower = MonetaryValue(amount=10.0, unit="m")
        mv_upper = MonetaryValue(amount=10.0, unit="M")
        assert mv_lower.normalized_amount == mv_upper.normalized_amount

    def test_normalized_amount_unknown_unit(self) -> None:
        """Unknown unit should default to multiplier of 1."""
        mv = MonetaryValue(amount=500.0, unit="XYZ")
        assert mv.normalized_amount == 500.0

    def test_custom_currency(self) -> None:
        """MonetaryValue should accept non-USD currencies."""
        mv = MonetaryValue(amount=10.0, currency="EUR", unit="M")
        assert mv.currency == "EUR"
        assert mv.normalized_amount == 10_000_000.0

    def test_zero_amount(self) -> None:
        """Zero amount should work correctly."""
        mv = MonetaryValue(amount=0.0, unit="M")
        assert mv.normalized_amount == 0.0

    def test_negative_amount(self) -> None:
        """Negative amounts should normalize correctly."""
        mv = MonetaryValue(amount=-2.5, unit="M")
        assert mv.normalized_amount == -2_500_000.0


# ---------------------------------------------------------------------------
# ExtractionResult Tests
# ---------------------------------------------------------------------------

class TestExtractionResult:
    """Tests for the ExtractionResult model."""

    def test_minimal_creation(self) -> None:
        """ExtractionResult should be created with only the required field."""
        result = ExtractionResult(company_name="MinimalCo")
        assert result.company_name == "MinimalCo"
        assert result.tagline is None
        assert result.stage is None
        assert result.extraction_confidence == 0.0
        assert result.source_page_count == 0

    def test_full_creation(self, sample_extraction_result: dict[str, Any]) -> None:
        """ExtractionResult should accept a full data payload."""
        result = ExtractionResult(**sample_extraction_result)
        assert result.company_name == "TechVenture AI"
        assert result.stage == DealStage.SERIES_A
        assert result.business_model == "SaaS"

    def test_extraction_with_team(self, sample_extraction_result: dict[str, Any]) -> None:
        """ExtractionResult should properly nest TeamInfo."""
        result = ExtractionResult(**sample_extraction_result)
        assert isinstance(result.team, TeamInfo)
        assert len(result.team.founders) == 1
        assert result.team.founders[0].name == "Jane Smith"
        assert result.team.total_employees == 45

    def test_extraction_with_financials(self, sample_extraction_result: dict[str, Any]) -> None:
        """ExtractionResult should properly nest FinancialMetrics."""
        result = ExtractionResult(**sample_extraction_result)
        assert isinstance(result.financials, FinancialMetrics)
        assert result.financials.revenue is not None
        assert result.financials.revenue.amount == 3.2
        assert result.financials.gross_margin == 0.82

    def test_extraction_with_market(self, sample_extraction_result: dict[str, Any]) -> None:
        """ExtractionResult should properly nest MarketData."""
        result = ExtractionResult(**sample_extraction_result)
        assert result.market.tam is not None
        assert result.market.tam.normalized_amount == 50_000_000_000.0

    def test_extraction_with_traction(self, sample_extraction_result: dict[str, Any]) -> None:
        """ExtractionResult should properly nest TractionMetrics."""
        result = ExtractionResult(**sample_extraction_result)
        assert result.traction.total_customers == 120
        assert len(result.traction.notable_customers) == 2

    def test_extraction_confidence_bounds(self) -> None:
        """extraction_confidence must be between 0 and 1."""
        result = ExtractionResult(company_name="BoundsCo", extraction_confidence=0.5)
        assert result.extraction_confidence == 0.5

        with pytest.raises(ValidationError):
            ExtractionResult(company_name="TooHigh", extraction_confidence=1.5)

        with pytest.raises(ValidationError):
            ExtractionResult(company_name="TooLow", extraction_confidence=-0.1)

    def test_extraction_missing_required_field(self) -> None:
        """ExtractionResult without company_name should fail validation."""
        with pytest.raises(ValidationError):
            ExtractionResult()  # type: ignore[call-arg]

    def test_extraction_default_lists(self) -> None:
        """Default list fields should be empty lists, not None."""
        result = ExtractionResult(company_name="DefaultCo")
        assert result.competitors == []
        assert result.competitive_advantages == []
        assert result.key_features == []
        assert result.technology_stack == []
        assert result.use_of_funds == []
        assert result.data_quality_flags == []
        assert result.missing_data_points == []

    def test_extraction_deal_stage_enum(self) -> None:
        """Stage field should accept valid DealStage enum values."""
        result = ExtractionResult(company_name="StageCo", stage="seed")
        assert result.stage == DealStage.SEED

    def test_extraction_invalid_stage(self) -> None:
        """Invalid stage value should raise validation error."""
        with pytest.raises(ValidationError):
            ExtractionResult(company_name="BadStage", stage="invalid")

    def test_extraction_serialization(self, sample_extraction_result: dict[str, Any]) -> None:
        """ExtractionResult should serialize to dict and back."""
        result = ExtractionResult(**sample_extraction_result)
        data = result.model_dump()
        result2 = ExtractionResult(**data)
        assert result2.company_name == result.company_name
        assert result2.extraction_confidence == result.extraction_confidence


# ---------------------------------------------------------------------------
# ConfidenceScore Tests
# ---------------------------------------------------------------------------

class TestConfidenceScore:
    """Tests for the ConfidenceScore model."""

    def test_basic_creation(self) -> None:
        """ConfidenceScore should accept score and confidence."""
        cs = ConfidenceScore(score=7.5, confidence=ConfidenceLevel.HIGH)
        assert cs.score == 7.5
        assert cs.confidence == ConfidenceLevel.HIGH

    def test_score_bounds(self) -> None:
        """Score must be between 0 and 10."""
        ConfidenceScore(score=0.0)  # min
        ConfidenceScore(score=10.0)  # max

        with pytest.raises(ValidationError):
            ConfidenceScore(score=-1.0)

        with pytest.raises(ValidationError):
            ConfidenceScore(score=11.0)

    def test_default_confidence(self) -> None:
        """Default confidence should be MEDIUM."""
        cs = ConfidenceScore(score=5.0)
        assert cs.confidence == ConfidenceLevel.MEDIUM

    def test_optional_reasoning(self) -> None:
        """Reasoning should be optional."""
        cs = ConfidenceScore(score=8.0, reasoning="Very strong.")
        assert cs.reasoning == "Very strong."

        cs2 = ConfidenceScore(score=8.0)
        assert cs2.reasoning is None


# ---------------------------------------------------------------------------
# FounderInfo Tests
# ---------------------------------------------------------------------------

class TestFounderInfo:
    """Tests for the FounderInfo model."""

    def test_minimal_creation(self) -> None:
        """FounderInfo requires only a name."""
        fi = FounderInfo(name="Alice Johnson")
        assert fi.name == "Alice Johnson"
        assert fi.title == ""
        assert fi.previous_companies == []

    def test_full_creation(self) -> None:
        """FounderInfo should accept all fields."""
        fi = FounderInfo(
            name="Bob Smith",
            title="CTO",
            background="Ex-Meta engineer",
            linkedin_url="https://linkedin.com/in/bobsmith",
            previous_companies=["Meta", "Google"],
            education="MIT CS",
            years_experience=15,
        )
        assert fi.title == "CTO"
        assert len(fi.previous_companies) == 2
        assert fi.years_experience == 15


# ---------------------------------------------------------------------------
# RiskItem Tests
# ---------------------------------------------------------------------------

class TestRiskItem:
    """Tests for the RiskItem model."""

    def test_creation(self) -> None:
        """RiskItem should accept all required fields."""
        risk = RiskItem(
            id="R001",
            title="Customer concentration",
            description="Top 3 customers = 40% revenue.",
            category=RiskCategory.FINANCIAL,
            severity=RiskSeverity.HIGH,
            likelihood=ConfidenceLevel.MEDIUM,
            impact="Revenue volatility",
        )
        assert risk.id == "R001"
        assert risk.severity == RiskSeverity.HIGH

    def test_missing_required_fields(self) -> None:
        """RiskItem without required fields should fail."""
        with pytest.raises(ValidationError):
            RiskItem(id="R002", title="Incomplete")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# ICMemo Tests
# ---------------------------------------------------------------------------

class TestICMemo:
    """Tests for the ICMemo (Investment Committee Memo) model."""

    def _build_confidence_score(
        self, score: float = 7.0, confidence: str = "high"
    ) -> dict:
        return {"score": score, "confidence": confidence, "reasoning": "Test."}

    def _build_analysis_result(self) -> dict[str, Any]:
        cs = self._build_confidence_score()
        ms = self._build_confidence_score(6.0, "medium")
        return {
            "business_model": {
                "overall_score": cs,
                "revenue_quality": cs,
                "margin_structure": cs,
                "scalability": cs,
                "defensibility": ms,
                "capital_efficiency": cs,
            },
            "market_analysis": {
                "market_score": cs,
                "tam_validity": ms,
                "market_timing": cs,
            },
            "competitive_analysis": {
                "competitive_score": cs,
                "differentiation_strength": cs,
                "barriers_to_entry": ms,
            },
            "growth_analysis": {
                "growth_score": cs,
                "growth_sustainability": cs,
            },
            "unit_economics_quality": cs,
            "team_assessment": cs,
            "investment_thesis": {
                "thesis_statement": "Strong opportunity in AI sales tools.",
                "thesis_confidence": "high",
            },
            "overall_attractiveness_score": cs,
            "analysis_confidence": 0.85,
        }

    def _build_risk_result(self) -> dict[str, Any]:
        return {
            "overall_risk_score": 4.5,
            "risk_adjusted_recommendation": "invest",
            "recommendation_reasoning": "Manageable risks.",
            "assessment_confidence": 0.80,
        }

    def _build_valuation_result(self) -> dict[str, Any]:
        mv = {"amount": 60.0, "currency": "USD", "unit": "M"}
        return {
            "valuation_range_low": {"amount": 45.0, "currency": "USD", "unit": "M"},
            "valuation_range_mid": mv,
            "valuation_range_high": {"amount": 80.0, "currency": "USD", "unit": "M"},
            "probability_weighted_value": mv,
            "valuation_confidence": "medium",
        }

    def test_ic_memo_creation(self) -> None:
        """Full ICMemo should be created from component parts."""
        memo = ICMemo(
            company_name="TestCo",
            executive_summary=ExecutiveSummary(
                company_overview="AI SaaS startup.",
                investment_highlights=["Strong growth", "Great team"],
                key_concerns=["Competition"],
                recommendation=RecommendationType.INVEST,
                recommendation_rationale="Good risk/reward.",
                valuation_summary="$60M pre-money is fair.",
                next_steps=["Deep-dive on churn"],
            ),
            extraction_result=ExtractionResult(company_name="TestCo"),
            analysis_result=AnalysisResult(**self._build_analysis_result()),
            risk_result=RiskResult(**self._build_risk_result()),
            valuation_result=ValuationResult(**self._build_valuation_result()),
            final_recommendation=RecommendationType.INVEST,
            conviction_level=ConfidenceLevel.HIGH,
            total_processing_time_seconds=45.0,
        )
        assert memo.company_name == "TestCo"
        assert memo.final_recommendation == RecommendationType.INVEST
        assert memo.conviction_level == ConfidenceLevel.HIGH

    def test_ic_memo_prepared_by_default(self) -> None:
        """ICMemo should default prepared_by to 'DealFlow AI Copilot'."""
        memo = ICMemo(
            company_name="DefaultsCo",
            executive_summary=ExecutiveSummary(
                company_overview="Test.",
                investment_highlights=[],
                key_concerns=[],
                recommendation=RecommendationType.PASS,
                recommendation_rationale="Test.",
                valuation_summary="N/A",
                next_steps=[],
            ),
            extraction_result=ExtractionResult(company_name="DefaultsCo"),
            analysis_result=AnalysisResult(**self._build_analysis_result()),
            risk_result=RiskResult(**self._build_risk_result()),
            valuation_result=ValuationResult(**self._build_valuation_result()),
            final_recommendation=RecommendationType.PASS,
            conviction_level=ConfidenceLevel.LOW,
            total_processing_time_seconds=30.0,
        )
        assert memo.prepared_by == "DealFlow AI Copilot"

    def test_ic_memo_missing_required(self) -> None:
        """ICMemo without required fields should fail."""
        with pytest.raises(ValidationError):
            ICMemo(company_name="Incomplete")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Enum Tests
# ---------------------------------------------------------------------------

class TestEnums:
    """Tests for enum values."""

    def test_deal_stage_values(self) -> None:
        """DealStage should have all expected values."""
        stages = [s.value for s in DealStage]
        assert "seed" in stages
        assert "series_a" in stages
        assert "growth" in stages

    def test_risk_severity_values(self) -> None:
        """RiskSeverity should have all expected values."""
        assert RiskSeverity.CRITICAL.value == "critical"
        assert RiskSeverity.HIGH.value == "high"
        assert RiskSeverity.MEDIUM.value == "medium"
        assert RiskSeverity.LOW.value == "low"

    def test_recommendation_type_values(self) -> None:
        """RecommendationType should include invest and pass options."""
        values = [r.value for r in RecommendationType]
        assert "strong_invest" in values
        assert "invest" in values
        assert "pass" in values
        assert "strong_pass" in values

    def test_agent_status_values(self) -> None:
        """AgentStatus should include pending, running, completed, failed."""
        values = [s.value for s in AgentStatus]
        assert "pending" in values
        assert "running" in values
        assert "completed" in values
        assert "failed" in values

    def test_confidence_level_values(self) -> None:
        """ConfidenceLevel should have high, medium, low."""
        assert ConfidenceLevel.HIGH.value == "high"
        assert ConfidenceLevel.MEDIUM.value == "medium"
        assert ConfidenceLevel.LOW.value == "low"

    def test_risk_category_values(self) -> None:
        """RiskCategory should have all expected categories."""
        values = [c.value for c in RiskCategory]
        assert "financial" in values
        assert "team" in values
        assert "market" in values
        assert "product" in values
        assert "legal" in values
        assert "operational" in values
        assert "consistency" in values
