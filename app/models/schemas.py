"""
Pydantic models and schemas for DealFlow AI Copilot.

This module defines all data structures used throughout the multi-agent system,
including extraction results, analysis outputs, risk assessments, valuations,
and the final IC memo structure.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================


class DealStage(str, Enum):
    """Investment stage of the company."""
    PRE_SEED = "pre_seed"
    SEED = "seed"
    SERIES_A = "series_a"
    SERIES_B = "series_b"
    SERIES_C = "series_c"
    GROWTH = "growth"
    LATE_STAGE = "late_stage"


class RiskSeverity(str, Enum):
    """Severity level for identified risks."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RiskCategory(str, Enum):
    """Category of risk."""
    FINANCIAL = "financial"
    TEAM = "team"
    MARKET = "market"
    PRODUCT = "product"
    LEGAL = "legal"
    OPERATIONAL = "operational"
    CONSISTENCY = "consistency"


class RecommendationType(str, Enum):
    """Investment recommendation types."""
    STRONG_INVEST = "strong_invest"
    INVEST = "invest"
    CONDITIONAL_INVEST = "conditional_invest"
    MORE_DILIGENCE = "more_diligence"
    PASS = "pass"
    STRONG_PASS = "strong_pass"


class ConfidenceLevel(str, Enum):
    """Confidence level for analysis."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AgentStatus(str, Enum):
    """Status of agent execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


# =============================================================================
# Base Models
# =============================================================================


class ConfidenceScore(BaseModel):
    """Score with confidence level."""
    score: float = Field(..., ge=0, le=10, description="Score from 0-10")
    confidence: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM)
    reasoning: Optional[str] = Field(default=None, description="Explanation for the score")


class MonetaryValue(BaseModel):
    """Monetary value with currency."""
    amount: float = Field(..., description="Numeric amount")
    currency: str = Field(default="USD", description="Currency code")
    unit: str = Field(default="", description="Unit (e.g., 'M' for millions, 'K' for thousands)")

    @property
    def normalized_amount(self) -> float:
        """Get amount normalized to base units."""
        multipliers = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}
        return self.amount * multipliers.get(self.unit.upper(), 1)


class DateRange(BaseModel):
    """Date range for financial periods."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    period_label: str = Field(default="", description="E.g., 'FY2023', 'Q1 2024'")


# =============================================================================
# Extraction Models
# =============================================================================


class FounderInfo(BaseModel):
    """Information about a founder or key team member."""
    name: str = Field(..., description="Full name")
    title: str = Field(default="", description="Role/title")
    background: Optional[str] = Field(default=None, description="Professional background")
    linkedin_url: Optional[str] = Field(default=None)
    previous_companies: list[str] = Field(default_factory=list)
    education: Optional[str] = Field(default=None)
    years_experience: Optional[int] = Field(default=None)


class TeamInfo(BaseModel):
    """Team composition information."""
    founders: list[FounderInfo] = Field(default_factory=list)
    total_employees: Optional[int] = Field(default=None)
    employee_growth_rate: Optional[float] = Field(default=None, description="YoY growth %")
    key_hires: list[str] = Field(default_factory=list, description="Notable recent hires")
    open_roles: list[str] = Field(default_factory=list, description="Key roles being hired")
    team_gaps: list[str] = Field(default_factory=list, description="Identified gaps in team")


class FinancialMetrics(BaseModel):
    """Core financial metrics extracted from pitch deck."""
    # Revenue metrics
    revenue: Optional[MonetaryValue] = Field(default=None, description="Current ARR/Revenue")
    revenue_growth_rate: Optional[float] = Field(default=None, description="YoY growth %")
    mrr: Optional[MonetaryValue] = Field(default=None, description="Monthly Recurring Revenue")
    arr: Optional[MonetaryValue] = Field(default=None, description="Annual Recurring Revenue")

    # Profitability
    gross_margin: Optional[float] = Field(default=None, description="Gross margin %")
    net_margin: Optional[float] = Field(default=None, description="Net margin %")
    ebitda: Optional[MonetaryValue] = Field(default=None)
    ebitda_margin: Optional[float] = Field(default=None)

    # Cash & Runway
    cash_on_hand: Optional[MonetaryValue] = Field(default=None)
    monthly_burn_rate: Optional[MonetaryValue] = Field(default=None)
    runway_months: Optional[int] = Field(default=None, description="Months of runway")

    # Fundraising
    total_raised: Optional[MonetaryValue] = Field(default=None)
    current_round_size: Optional[MonetaryValue] = Field(default=None)
    pre_money_valuation: Optional[MonetaryValue] = Field(default=None)
    post_money_valuation: Optional[MonetaryValue] = Field(default=None)

    # Historical
    revenue_history: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Historical revenue data points"
    )


class UnitEconomics(BaseModel):
    """Unit economics metrics."""
    cac: Optional[MonetaryValue] = Field(default=None, description="Customer Acquisition Cost")
    ltv: Optional[MonetaryValue] = Field(default=None, description="Lifetime Value")
    ltv_cac_ratio: Optional[float] = Field(default=None)
    payback_period_months: Optional[int] = Field(default=None)

    # SaaS specific
    arpu: Optional[MonetaryValue] = Field(default=None, description="Average Revenue Per User")
    net_revenue_retention: Optional[float] = Field(default=None, description="NRR %")
    gross_revenue_retention: Optional[float] = Field(default=None, description="GRR %")
    churn_rate: Optional[float] = Field(default=None, description="Monthly churn %")

    # Other
    aov: Optional[MonetaryValue] = Field(default=None, description="Average Order Value")
    purchase_frequency: Optional[float] = Field(default=None)


class MarketData(BaseModel):
    """Market size and opportunity data."""
    tam: Optional[MonetaryValue] = Field(default=None, description="Total Addressable Market")
    sam: Optional[MonetaryValue] = Field(default=None, description="Serviceable Addressable Market")
    som: Optional[MonetaryValue] = Field(default=None, description="Serviceable Obtainable Market")
    tam_source: Optional[str] = Field(default=None, description="Source of TAM estimate")
    market_growth_rate: Optional[float] = Field(default=None, description="Market CAGR %")
    market_description: Optional[str] = Field(default=None)


class TractionMetrics(BaseModel):
    """Traction and growth metrics."""
    # Customers
    total_customers: Optional[int] = Field(default=None)
    customer_growth_rate: Optional[float] = Field(default=None, description="YoY growth %")
    enterprise_customers: Optional[int] = Field(default=None)
    smb_customers: Optional[int] = Field(default=None)
    notable_customers: list[str] = Field(default_factory=list)

    # Users
    total_users: Optional[int] = Field(default=None)
    mau: Optional[int] = Field(default=None, description="Monthly Active Users")
    dau: Optional[int] = Field(default=None, description="Daily Active Users")
    user_growth_rate: Optional[float] = Field(default=None)

    # Engagement
    engagement_rate: Optional[float] = Field(default=None)
    conversion_rate: Optional[float] = Field(default=None)

    # Other
    gmv: Optional[MonetaryValue] = Field(default=None, description="Gross Merchandise Value")
    transactions_count: Optional[int] = Field(default=None)


class CompetitorInfo(BaseModel):
    """Information about a competitor."""
    name: str
    description: Optional[str] = Field(default=None)
    funding_raised: Optional[MonetaryValue] = Field(default=None)
    valuation: Optional[MonetaryValue] = Field(default=None)
    market_position: Optional[str] = Field(default=None)
    key_differentiators: list[str] = Field(default_factory=list)


class ExtractionResult(BaseModel):
    """Complete extraction result from pitch deck."""
    # Company basics
    company_name: str = Field(..., description="Company name")
    tagline: Optional[str] = Field(default=None, description="Company tagline/one-liner")
    description: Optional[str] = Field(default=None, description="Company description")
    website: Optional[str] = Field(default=None)
    founded_year: Optional[int] = Field(default=None)
    headquarters: Optional[str] = Field(default=None)

    # Classification
    industry: Optional[str] = Field(default=None)
    sector: Optional[str] = Field(default=None)
    business_model: Optional[str] = Field(default=None, description="E.g., SaaS, Marketplace, D2C")
    stage: Optional[DealStage] = Field(default=None)

    # Core data
    team: TeamInfo = Field(default_factory=TeamInfo)
    financials: FinancialMetrics = Field(default_factory=FinancialMetrics)
    unit_economics: UnitEconomics = Field(default_factory=UnitEconomics)
    market: MarketData = Field(default_factory=MarketData)
    traction: TractionMetrics = Field(default_factory=TractionMetrics)

    # Competitive
    competitors: list[CompetitorInfo] = Field(default_factory=list)
    competitive_advantages: list[str] = Field(default_factory=list)

    # Product
    product_description: Optional[str] = Field(default=None)
    key_features: list[str] = Field(default_factory=list)
    technology_stack: list[str] = Field(default_factory=list)

    # Ask
    funding_ask: Optional[MonetaryValue] = Field(default=None)
    use_of_funds: list[dict[str, Any]] = Field(default_factory=list)

    # Metadata
    extraction_confidence: float = Field(default=0.0, ge=0, le=1)
    data_quality_flags: list[str] = Field(default_factory=list)
    missing_data_points: list[str] = Field(default_factory=list)
    source_page_count: int = Field(default=0)


# =============================================================================
# Analysis Models
# =============================================================================


class BusinessModelScore(BaseModel):
    """Detailed business model evaluation."""
    overall_score: ConfidenceScore
    revenue_quality: ConfidenceScore = Field(description="Quality/predictability of revenue")
    margin_structure: ConfidenceScore = Field(description="Margin profile assessment")
    scalability: ConfidenceScore = Field(description="Ability to scale efficiently")
    defensibility: ConfidenceScore = Field(description="Competitive moats")
    capital_efficiency: ConfidenceScore = Field(description="Capital efficiency")


class MarketAnalysis(BaseModel):
    """Market opportunity assessment."""
    market_score: ConfidenceScore
    tam_validity: ConfidenceScore = Field(description="Believability of TAM claims")
    market_timing: ConfidenceScore = Field(description="Right time for this market")
    market_dynamics: Optional[str] = Field(default=None, description="Key market trends")
    tailwinds: list[str] = Field(default_factory=list)
    headwinds: list[str] = Field(default_factory=list)


class CompetitiveAnalysis(BaseModel):
    """Competitive positioning assessment."""
    competitive_score: ConfidenceScore
    market_position: Optional[str] = Field(default=None, description="Leader/Challenger/Niche")
    differentiation_strength: ConfidenceScore
    barriers_to_entry: ConfidenceScore
    competitive_threats: list[str] = Field(default_factory=list)
    sustainable_advantages: list[str] = Field(default_factory=list)


class GrowthAnalysis(BaseModel):
    """Growth trajectory analysis."""
    growth_score: ConfidenceScore
    historical_growth_rate: Optional[float] = Field(default=None)
    projected_growth_rate: Optional[float] = Field(default=None)
    growth_drivers: list[str] = Field(default_factory=list)
    growth_constraints: list[str] = Field(default_factory=list)
    growth_sustainability: ConfidenceScore


class ComparableCompany(BaseModel):
    """Comparable company for benchmarking."""
    name: str
    similarity_score: float = Field(ge=0, le=1)
    outcome: Optional[str] = Field(default=None, description="IPO, Acquired, etc.")
    valuation_at_similar_stage: Optional[MonetaryValue] = Field(default=None)
    key_similarities: list[str] = Field(default_factory=list)
    key_differences: list[str] = Field(default_factory=list)


class InvestmentThesis(BaseModel):
    """Core investment thesis."""
    thesis_statement: str = Field(..., description="One-paragraph investment thesis")
    key_beliefs: list[str] = Field(default_factory=list, description="What must be true")
    upside_drivers: list[str] = Field(default_factory=list)
    key_concerns: list[str] = Field(default_factory=list)
    thesis_confidence: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM)


class AnalysisResult(BaseModel):
    """Complete analysis result from Analysis Agent."""
    # Core assessments
    business_model: BusinessModelScore
    market_analysis: MarketAnalysis
    competitive_analysis: CompetitiveAnalysis
    growth_analysis: GrowthAnalysis
    unit_economics_quality: ConfidenceScore
    team_assessment: ConfidenceScore

    # Investment thesis
    investment_thesis: InvestmentThesis

    # Comparables
    comparable_companies: list[ComparableCompany] = Field(default_factory=list)

    # Scores
    overall_attractiveness_score: ConfidenceScore

    # Summary
    key_strengths: list[str] = Field(default_factory=list)
    key_weaknesses: list[str] = Field(default_factory=list)
    critical_questions: list[str] = Field(default_factory=list, description="Questions for management")

    # Metadata
    analysis_confidence: float = Field(default=0.0, ge=0, le=1)


# =============================================================================
# Risk Models
# =============================================================================


class RiskItem(BaseModel):
    """Individual identified risk."""
    id: str = Field(..., description="Unique risk identifier")
    title: str = Field(..., description="Brief risk title")
    description: str = Field(..., description="Detailed risk description")
    category: RiskCategory
    severity: RiskSeverity
    likelihood: ConfidenceLevel = Field(description="Likelihood of risk materializing")
    impact: str = Field(description="Potential impact if risk materializes")
    mitigation: Optional[str] = Field(default=None, description="Potential mitigation")
    evidence: list[str] = Field(default_factory=list, description="Supporting evidence")
    affected_areas: list[str] = Field(default_factory=list)


class RiskSummary(BaseModel):
    """Risk summary by category."""
    category: RiskCategory
    risk_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    top_risks: list[str] = Field(default_factory=list, description="Top risk titles")


class DataConsistencyCheck(BaseModel):
    """Data consistency verification."""
    check_name: str
    passed: bool
    discrepancy: Optional[str] = Field(default=None)
    values_compared: dict[str, Any] = Field(default_factory=dict)


class RiskResult(BaseModel):
    """Complete risk assessment result."""
    # All risks
    risks: list[RiskItem] = Field(default_factory=list)

    # Summaries by category
    risk_summaries: list[RiskSummary] = Field(default_factory=list)

    # Data consistency
    consistency_checks: list[DataConsistencyCheck] = Field(default_factory=list)
    data_integrity_score: float = Field(default=0.0, ge=0, le=1)

    # Overall assessment
    overall_risk_score: float = Field(default=0.0, ge=0, le=10, description="0=low risk, 10=high risk")
    risk_adjusted_recommendation: RecommendationType
    recommendation_reasoning: str = Field(default="")

    # Critical items
    deal_breakers: list[str] = Field(default_factory=list)
    must_verify_items: list[str] = Field(default_factory=list)

    # Counts
    total_risks: int = Field(default=0)
    critical_risks: int = Field(default=0)
    high_risks: int = Field(default=0)

    # Metadata
    assessment_confidence: float = Field(default=0.0, ge=0, le=1)


# =============================================================================
# Valuation Models
# =============================================================================


class RevenueMultipleValuation(BaseModel):
    """Revenue multiple based valuation."""
    methodology: str = Field(default="Revenue Multiple")
    base_revenue: MonetaryValue
    comparable_multiple_range: tuple[float, float] = Field(description="(low, high)")
    applied_multiple: float
    multiple_adjustments: dict[str, float] = Field(
        default_factory=dict,
        description="Adjustments for growth, margins, etc."
    )
    implied_valuation: MonetaryValue
    reasoning: str = Field(default="")


class ComparableValuation(BaseModel):
    """Comparable company based valuation."""
    methodology: str = Field(default="Comparable Analysis")
    comparables_used: list[str] = Field(default_factory=list)
    median_multiple: float
    implied_valuation_range: tuple[MonetaryValue, MonetaryValue]
    adjustments_made: list[str] = Field(default_factory=list)


class DCFValuation(BaseModel):
    """Simplified DCF valuation."""
    methodology: str = Field(default="Discounted Cash Flow")
    projection_years: int = Field(default=5)
    revenue_cagr_assumption: float
    terminal_growth_rate: float
    discount_rate: float
    terminal_value: MonetaryValue
    enterprise_value: MonetaryValue
    key_assumptions: dict[str, Any] = Field(default_factory=dict)


class SensitivityScenario(BaseModel):
    """Sensitivity analysis scenario."""
    variable_name: str
    base_value: float
    adjusted_value: float
    resulting_valuation: MonetaryValue
    change_percentage: float


class ValuationScenario(BaseModel):
    """Valuation scenario (bull/base/bear)."""
    scenario_name: str = Field(description="E.g., 'Bull', 'Base', 'Bear'")
    probability: float = Field(ge=0, le=1, description="Probability weight")
    valuation: MonetaryValue
    key_assumptions: list[str] = Field(default_factory=list)
    implied_multiple: float


class ValuationResult(BaseModel):
    """Complete valuation result."""
    # Methodologies
    revenue_multiple: Optional[RevenueMultipleValuation] = Field(default=None)
    comparable_analysis: Optional[ComparableValuation] = Field(default=None)
    dcf: Optional[DCFValuation] = Field(default=None)

    # Scenarios
    scenarios: list[ValuationScenario] = Field(default_factory=list)

    # Summary range
    valuation_range_low: MonetaryValue
    valuation_range_mid: MonetaryValue
    valuation_range_high: MonetaryValue
    probability_weighted_value: MonetaryValue

    # Sensitivity
    sensitivity_analysis: list[SensitivityScenario] = Field(default_factory=list)

    # vs Ask
    ask_vs_valuation: str = Field(default="", description="How ask compares to our valuation")
    implied_discount_premium: float = Field(
        default=0.0,
        description="Positive = discount, negative = premium"
    )

    # Investment return
    target_return_multiple: Optional[float] = Field(default=None)
    target_irr: Optional[float] = Field(default=None)

    # Confidence
    valuation_confidence: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM)
    key_valuation_risks: list[str] = Field(default_factory=list)

    # Metadata
    methodologies_used: list[str] = Field(default_factory=list)
    assessment_date: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Orchestration Models
# =============================================================================


class AgentExecutionStatus(BaseModel):
    """Status of individual agent execution."""
    agent_name: str
    status: AgentStatus
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    duration_seconds: Optional[float] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    retry_count: int = Field(default=0)


class OrchestratorProgress(BaseModel):
    """Progress update from orchestrator."""
    overall_status: AgentStatus
    current_phase: str = Field(description="E.g., 'extraction', 'parallel_analysis', 'synthesis'")
    progress_percentage: float = Field(ge=0, le=100)
    agents_status: list[AgentExecutionStatus] = Field(default_factory=list)
    started_at: datetime
    estimated_completion: Optional[datetime] = Field(default=None)
    messages: list[str] = Field(default_factory=list, description="Status messages")


# =============================================================================
# Final Output Models
# =============================================================================


class ExecutiveSummary(BaseModel):
    """Executive summary for IC memo."""
    company_overview: str
    investment_highlights: list[str]
    key_concerns: list[str]
    recommendation: RecommendationType
    recommendation_rationale: str
    valuation_summary: str
    next_steps: list[str]


class ICMemo(BaseModel):
    """Complete Investment Committee Memo."""
    # Header
    company_name: str
    memo_date: datetime = Field(default_factory=datetime.utcnow)
    prepared_by: str = Field(default="DealFlow AI Copilot")

    # Executive Summary
    executive_summary: ExecutiveSummary

    # All agent outputs
    extraction_result: ExtractionResult
    analysis_result: AnalysisResult
    risk_result: RiskResult
    valuation_result: ValuationResult

    # Final recommendation
    final_recommendation: RecommendationType
    conviction_level: ConfidenceLevel

    # Diligence workstreams
    diligence_items: list[str] = Field(default_factory=list)
    key_questions_for_management: list[str] = Field(default_factory=list)

    # Metadata
    total_processing_time_seconds: float
    model_version: str = Field(default="1.0.0")


# =============================================================================
# API Request/Response Models
# =============================================================================


class AnalysisRequest(BaseModel):
    """Request to analyze a pitch deck."""
    file_id: Optional[str] = Field(default=None, description="ID of uploaded file")
    file_path: Optional[str] = Field(default=None, description="Path to file")
    company_name: Optional[str] = Field(default=None, description="Override company name")
    additional_context: Optional[str] = Field(default=None, description="Extra context")
    fast_mode: bool = Field(default=False, description="Skip some analyses for speed")


class AnalysisResponse(BaseModel):
    """Response from analysis request."""
    analysis_id: str
    status: AgentStatus
    message: str
    progress: Optional[OrchestratorProgress] = Field(default=None)
    result: Optional[ICMemo] = Field(default=None)
    error: Optional[str] = Field(default=None)


class UploadResponse(BaseModel):
    """Response from file upload."""
    file_id: str
    filename: str
    file_path: str
    file_size_bytes: int
    mime_type: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
