"""
Prompt templates for the Risk Agent.

These prompts guide systematic risk identification across financial, team,
market, and operational dimensions, with severity prioritization.
"""

RISK_SYSTEM_PROMPT = """You are a risk management expert at a top-tier investment firm.
Your role is to systematically identify and assess risks in potential investments.

Your approach is:
- Comprehensive and systematic - no stone unturned
- Severity-focused - prioritize what matters most
- Evidence-based - risks must be supported by data
- Practical - focus on actionable risk assessment
- Skeptical - assume the worst until proven otherwise

You've seen hundreds of deals and know the patterns of failure.
Your job is to protect capital by identifying risks before they materialize.
"""

FINANCIAL_RISK_PROMPT = """Identify all financial risks in this company.

FINANCIAL DATA:
{financial_data}

Analyze these risk categories:

1. BURN RATE & RUNWAY
   - How long until cash runs out?
   - Is burn rate sustainable?
   - Dependency on raising more capital?

2. UNIT ECONOMICS QUALITY
   - Are unit economics proven or projected?
   - LTV/CAC ratio credibility?
   - Payback period realism?

3. REVENUE CONCENTRATION
   - Customer concentration risk?
   - Revenue source diversity?
   - Contract renewal risks?

4. PROJECTION REALISM
   - Are growth projections achievable?
   - What assumptions underlie projections?
   - Historical vs. projected comparison?

5. CAPITAL STRUCTURE
   - Existing investor rights?
   - Liquidation preferences?
   - Dilution implications?

For each risk found, provide:
- Risk ID (unique identifier)
- Title (brief name)
- Description (detailed explanation)
- Severity (critical/high/medium/low)
- Likelihood (high/medium/low)
- Impact (what happens if risk materializes)
- Evidence (data supporting this risk)
- Mitigation (potential ways to address)

Return a JSON array of risk objects:
[
    {
        "id": "FIN-001",
        "title": "string",
        "description": "string",
        "category": "financial",
        "severity": "critical/high/medium/low",
        "likelihood": "high/medium/low",
        "impact": "string",
        "mitigation": "string or null",
        "evidence": ["string"],
        "affected_areas": ["string"]
    }
]
"""

TEAM_RISK_PROMPT = """Identify all team-related risks.

TEAM DATA:
{team_data}

Analyze these risk categories:

1. FOUNDER RISKS
   - First-time founders without relevant experience?
   - Past failures or concerning history?
   - Founder conflicts or departures?
   - Single founder dependency?

2. KEY PERSON DEPENDENCY
   - Over-reliance on specific individuals?
   - Succession planning?
   - Non-compete/non-solicit issues?

3. TEAM GAPS
   - Missing critical roles?
   - Weak functional areas?
   - Ability to attract talent?

4. ORGANIZATIONAL RISKS
   - Scaling challenges?
   - Culture issues?
   - High turnover indicators?

5. BACKGROUND CONCERNS
   - Anything concerning in backgrounds?
   - Exaggerated credentials?
   - Reference check flags?

Return a JSON array of risk objects with category "team".
"""

MARKET_RISK_PROMPT = """Identify all market-related risks.

MARKET DATA:
{market_data}

COMPETITIVE DATA:
{competitive_data}

Analyze these risk categories:

1. COMPETITION RISKS
   - Well-funded competitors?
   - Big tech threat?
   - Incumbent response?
   - Price competition?

2. MARKET TIMING
   - Too early? Too late?
   - Market readiness?
   - Adoption barriers?

3. MARKET SIZE RISKS
   - Is the market as big as claimed?
   - Market definition issues?
   - Addressable market shrinking?

4. REGULATORY RISKS
   - Current regulations?
   - Pending legislation?
   - Compliance requirements?
   - Industry-specific rules?

5. MACRO RISKS
   - Economic sensitivity?
   - Interest rate impact?
   - Geopolitical factors?

Return a JSON array of risk objects with category "market".
"""

OPERATIONAL_RISK_PROMPT = """Identify operational and execution risks.

COMPANY DATA:
{company_data}

Analyze these risk categories:

1. EXECUTION RISKS
   - Can they deliver on the plan?
   - Track record of execution?
   - Complexity of operations?

2. TECHNOLOGY RISKS
   - Technical debt?
   - Scalability issues?
   - Security vulnerabilities?
   - Dependency on key tech?

3. SUPPLY CHAIN RISKS
   - Vendor dependencies?
   - Single points of failure?
   - Geographic concentration?

4. LEGAL RISKS
   - IP ownership issues?
   - Pending litigation?
   - Contract risks?
   - Employment issues?

5. PRODUCT RISKS
   - Product-market fit proven?
   - Development timeline risks?
   - Customer satisfaction issues?

Return a JSON array of risk objects with categories "operational", "legal", or "product".
"""

DATA_CONSISTENCY_PROMPT = """Cross-check data for inconsistencies and red flags.

EXTRACTED DATA:
{extraction_data}

Perform these consistency checks:

1. FINANCIAL MATH
   - MRR × 12 = ARR?
   - Revenue growth matches historical data?
   - Burn rate × runway = cash?
   - Margins are internally consistent?

2. METRIC CONSISTENCY
   - Customer count × ARPU ≈ Revenue?
   - CAC × customers ≈ S&M spend?
   - Growth rate matches period-over-period?

3. CLAIM VERIFICATION
   - Do stated metrics match shown charts?
   - Are year-over-year claims accurate?
   - Do percentages add to 100%?

4. RED FLAGS
   - Cherry-picked metrics?
   - Missing standard metrics?
   - Unusual metric definitions?
   - Inconsistent time periods?

For each check, return:
{
    "check_name": "string",
    "passed": true/false,
    "discrepancy": "string explaining issue or null",
    "values_compared": {
        "stated_value": "value from deck",
        "calculated_value": "your calculation"
    }
}

Return a JSON object:
{
    "consistency_checks": [check objects],
    "data_integrity_score": "number 0-1",
    "critical_discrepancies": ["string"],
    "red_flags": ["string"]
}
"""

RISK_SYNTHESIS_PROMPT = """Synthesize all identified risks into a final assessment.

FINANCIAL RISKS:
{financial_risks}

TEAM RISKS:
{team_risks}

MARKET RISKS:
{market_risks}

OPERATIONAL RISKS:
{operational_risks}

DATA CONSISTENCY:
{consistency_results}

Create a comprehensive risk summary:

1. OVERALL RISK SCORE (0-10, where 10 is highest risk)
   - Weight critical risks heavily
   - Consider likelihood and impact
   - Factor in mitigation possibilities

2. DEAL BREAKERS
   - Are there any risks that should stop the deal?
   - What would need to change?

3. RISK-ADJUSTED RECOMMENDATION
   - strong_invest: Low risk, clear opportunity
   - invest: Acceptable risks, good opportunity
   - conditional_invest: Investable if key risks mitigated
   - more_diligence: Need more information
   - pass: Risks outweigh opportunity
   - strong_pass: Critical risks, do not proceed

4. MUST-VERIFY ITEMS
   - What needs to be confirmed in diligence?
   - Priority verification items?

Return a JSON object:
{
    "overall_risk_score": "number 0-10",
    "risk_adjusted_recommendation": "string (one of the types above)",
    "recommendation_reasoning": "string explaining the recommendation",
    "deal_breakers": ["string"],
    "must_verify_items": ["string"],
    "total_risks": "number",
    "critical_risks": "number",
    "high_risks": "number",
    "risk_summaries_by_category": [
        {
            "category": "financial/team/market/operational/legal/product/consistency",
            "risk_count": "number",
            "critical_count": "number",
            "high_count": "number",
            "medium_count": "number",
            "low_count": "number",
            "top_risks": ["string - titles of top risks"]
        }
    ],
    "assessment_confidence": "number 0-1"
}
"""
