"""
Simplified Output Schema for DealFlow AI Copilot.

Clean, categorized output structure where each agent's work is clearly separated
with methodology explanations and a combined summary view.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class Recommendation(str, Enum):
    """Investment recommendation levels."""
    STRONG_BUY = "Strong Buy"
    BUY = "Buy"
    HOLD = "Hold"
    PASS = "Pass"
    STRONG_PASS = "Strong Pass"


class RiskLevel(str, Enum):
    """Risk severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# =============================================================================
# EXTRACTION OUTPUT
# =============================================================================

class CompanyBasics(BaseModel):
    """Basic company information."""
    name: str
    tagline: Optional[str] = None
    industry: Optional[str] = None
    stage: Optional[str] = None  # seed, series_a, series_b, etc.
    business_model: Optional[str] = None  # saas, marketplace, d2c, etc.
    founded_year: Optional[int] = None
    headquarters: Optional[str] = None
    website: Optional[str] = None


class FinancialMetrics(BaseModel):
    """Key financial metrics."""
    revenue_arr: Optional[float] = Field(None, description="ARR in millions USD")
    growth_rate: Optional[float] = Field(None, description="YoY growth as percentage")
    gross_margin: Optional[float] = Field(None, description="Gross margin as percentage")
    burn_rate: Optional[float] = Field(None, description="Monthly burn in millions USD")
    runway_months: Optional[int] = None
    total_raised: Optional[float] = Field(None, description="Total raised in millions USD")
    asking_amount: Optional[float] = Field(None, description="Current round ask in millions USD")
    valuation_ask: Optional[float] = Field(None, description="Pre-money valuation in millions USD")


class TeamMember(BaseModel):
    """Team member information."""
    name: str
    role: Optional[str] = None
    background: Optional[str] = None


class MarketInfo(BaseModel):
    """Market information."""
    tam: Optional[float] = Field(None, description="TAM in billions USD")
    sam: Optional[float] = Field(None, description="SAM in billions USD")
    target_customers: Optional[str] = None
    competitors: list[str] = Field(default_factory=list)


class ExtractionOutput(BaseModel):
    """
    Output from the Extraction Agent.

    What it does: Reads all uploaded documents and extracts structured data.
    """
    agent_name: str = "Extraction Agent"
    methodology: str = Field(
        default="Analyzes document text and images using AI vision to extract "
                "company information, financial metrics, team data, and market details. "
                "Cross-references data across multiple documents for accuracy."
    )

    # Extracted data
    company: CompanyBasics
    financials: FinancialMetrics
    team: list[TeamMember] = Field(default_factory=list)
    team_size: Optional[int] = None
    market: MarketInfo

    # Metadata
    documents_processed: int = 0
    extraction_confidence: float = Field(0.0, ge=0, le=1)
    data_gaps: list[str] = Field(default_factory=list, description="Missing data points")


# =============================================================================
# ANALYSIS OUTPUT
# =============================================================================

class ScoreWithReasoning(BaseModel):
    """A score with explanation."""
    score: float = Field(..., ge=0, le=10)
    reasoning: str


class AnalysisOutput(BaseModel):
    """
    Output from the Analysis Agent.

    What it does: Evaluates business model quality, market opportunity,
    competitive positioning, and growth potential.
    """
    agent_name: str = "Analysis Agent"
    methodology: str = Field(
        default="Evaluates the company across four dimensions using PE/VC frameworks: "
                "1) Business Model (revenue quality, margins, scalability), "
                "2) Market (TAM validity, timing, dynamics), "
                "3) Competition (positioning, differentiation, barriers), "
                "4) Growth (sustainability, drivers, constraints). "
                "Each dimension scored 0-10 with detailed reasoning."
    )

    # Scores with reasoning
    business_model_score: ScoreWithReasoning
    market_score: ScoreWithReasoning
    competitive_score: ScoreWithReasoning
    growth_score: ScoreWithReasoning

    # Overall
    overall_score: float = Field(..., ge=0, le=10)

    # Key findings
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)
    threats: list[str] = Field(default_factory=list)


# =============================================================================
# RISK OUTPUT
# =============================================================================

class Risk(BaseModel):
    """Individual risk item."""
    category: str  # financial, team, market, operational
    title: str
    description: str
    severity: RiskLevel
    likelihood: str  # high, medium, low
    mitigation: Optional[str] = None


class RiskOutput(BaseModel):
    """
    Output from the Risk Agent.

    What it does: Identifies and prioritizes risks across financial, team,
    market, and operational dimensions.
    """
    agent_name: str = "Risk Agent"
    methodology: str = Field(
        default="Systematically identifies risks across four categories: "
                "1) Financial (burn, unit economics, projections), "
                "2) Team (founder experience, key person dependency, gaps), "
                "3) Market (competition, timing, regulation), "
                "4) Operational (execution, technology, legal). "
                "Each risk rated by severity and likelihood."
    )

    # Risks by category
    risks: list[Risk] = Field(default_factory=list)

    # Summary counts
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0

    # Overall risk assessment
    overall_risk_score: float = Field(..., ge=0, le=10, description="0=low risk, 10=high risk")
    deal_breakers: list[str] = Field(default_factory=list)
    must_verify: list[str] = Field(default_factory=list, description="Items to verify in due diligence")


# =============================================================================
# VALUATION OUTPUT
# =============================================================================

class ValuationMethod(BaseModel):
    """Single valuation methodology result."""
    method_name: str
    value_low: float  # in millions
    value_mid: float
    value_high: float
    key_assumptions: list[str]


class ValuationOutput(BaseModel):
    """
    Output from the Valuation Agent.

    What it does: Calculates company valuation using multiple methodologies
    and provides a recommended range.
    """
    agent_name: str = "Valuation Agent"
    methodology: str = Field(
        default="Applies three valuation approaches: "
                "1) Revenue Multiples (based on growth rate, margins, comparable SaaS companies), "
                "2) Comparable Analysis (recent funding rounds of similar companies), "
                "3) Scenario Analysis (bull/base/bear cases with probabilities). "
                "Final range is probability-weighted across methodologies."
    )

    # Individual method results
    methods: list[ValuationMethod] = Field(default_factory=list)

    # Final range (in millions USD)
    valuation_low: float
    valuation_mid: float
    valuation_high: float

    # Comparison to ask
    company_ask: Optional[float] = Field(None, description="Company's asking valuation in millions")
    ask_vs_our_value: Optional[str] = None  # "Fair", "Expensive", "Attractive"
    premium_discount_pct: Optional[float] = None  # Positive = premium, negative = discount


# =============================================================================
# COMBINED SUMMARY OUTPUT
# =============================================================================

class DealSummary(BaseModel):
    """
    Combined Summary of all agent outputs.

    The executive-level view for quick decision making.
    """
    # Header
    company_name: str
    analysis_date: datetime = Field(default_factory=datetime.utcnow)

    # One-line summary
    headline: str = Field(..., description="One sentence summary of the opportunity")

    # Recommendation
    recommendation: Recommendation
    conviction: str  # "High", "Medium", "Low"

    # Key metrics at a glance
    key_metrics: dict[str, Any] = Field(
        default_factory=dict,
        description="Quick reference metrics: ARR, Growth, Valuation, etc."
    )

    # Scoring summary
    analysis_score: float = Field(..., ge=0, le=10)
    risk_score: float = Field(..., ge=0, le=10, description="Lower is better")

    # Top 3 reasons to invest
    reasons_to_invest: list[str] = Field(default_factory=list)

    # Top 3 concerns
    key_concerns: list[str] = Field(default_factory=list)

    # Valuation summary
    valuation_range: str  # e.g., "$40M - $60M"
    valuation_vs_ask: Optional[str] = None

    # Next steps
    diligence_priorities: list[str] = Field(default_factory=list)
    questions_for_founders: list[str] = Field(default_factory=list)


# =============================================================================
# FULL ANALYSIS RESULT
# =============================================================================

class FullAnalysisResult(BaseModel):
    """
    Complete analysis result with all agent outputs and summary.

    Structure:
    - summary: Executive summary for quick decisions
    - extraction: Raw data extracted from documents
    - analysis: Business evaluation scores
    - risks: Risk assessment
    - valuation: Valuation analysis
    """
    # The summary tab - what executives see first
    summary: DealSummary

    # Individual agent outputs - detailed view
    extraction: ExtractionOutput
    analysis: AnalysisOutput
    risks: RiskOutput
    valuation: ValuationOutput

    # Processing metadata
    total_processing_time_seconds: float
    documents_analyzed: list[str] = Field(default_factory=list)
    model_version: str = "2.0.0"
