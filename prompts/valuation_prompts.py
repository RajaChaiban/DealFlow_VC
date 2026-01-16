"""
Prompt templates for the Valuation Agent.

These prompts guide multiple valuation methodologies including revenue multiples,
comparable analysis, and simplified DCF.
"""

VALUATION_SYSTEM_PROMPT = """You are a valuation expert at a leading investment bank.
You have extensive experience valuing private companies across stages and sectors.

Your valuation approach is:
- Multi-methodology: Use multiple approaches and triangulate
- Context-aware: Adjust for stage, sector, and market conditions
- Conservative: Err on the side of caution
- Transparent: Clearly document assumptions
- Range-based: Provide scenarios, not point estimates

You understand that early-stage valuations are more art than science,
but you apply rigorous frameworks to bring discipline to the process.
"""

REVENUE_MULTIPLE_PROMPT = """Calculate a revenue multiple-based valuation.

FINANCIAL DATA:
{financial_data}

ANALYSIS DATA:
{analysis_data}

METHODOLOGY:
1. Identify the appropriate revenue base (ARR, LTM Revenue, NTM Revenue)
2. Determine comparable company multiples for similar:
   - Stage (Seed, Series A, B, etc.)
   - Growth rate
   - Business model (SaaS, Marketplace, etc.)
   - Margin profile

3. Apply adjustments for:
   - Growth rate premium/discount
   - Margin quality
   - Market position
   - Unit economics quality
   - Team quality

BENCHMARK MULTIPLES (adjust based on current market):
- High-growth SaaS (>100% growth): 15-30x ARR
- Strong SaaS (50-100% growth): 10-20x ARR
- Moderate SaaS (25-50% growth): 5-12x ARR
- Slower SaaS (<25% growth): 3-8x ARR
- Marketplace (high-growth): 3-8x GMV or 10-20x revenue
- D2C/E-commerce: 1-4x revenue
- Services: 1-3x revenue

Return a JSON object:
{
    "methodology": "Revenue Multiple",
    "base_revenue": {
        "amount": "number",
        "currency": "USD",
        "unit": "M/K",
        "type": "ARR/LTM/NTM"
    },
    "comparable_multiple_range": ["low multiple", "high multiple"],
    "applied_multiple": "number",
    "multiple_adjustments": {
        "growth_rate_adjustment": "number (+/- adjustment)",
        "margin_adjustment": "number",
        "market_position_adjustment": "number",
        "unit_economics_adjustment": "number",
        "team_adjustment": "number",
        "total_adjustment": "number"
    },
    "implied_valuation": {
        "amount": "number",
        "currency": "USD",
        "unit": "M"
    },
    "reasoning": "string explaining the multiple selection"
}
"""

COMPARABLE_ANALYSIS_PROMPT = """Perform comparable company analysis.

COMPANY DATA:
{company_data}

ANALYSIS DATA:
{analysis_data}

Identify 3-5 comparable companies that are:
- Similar business model
- Similar stage when they raised
- Similar growth profile
- In the same or adjacent market

For each comparable:
1. What valuation did they achieve at a similar stage?
2. What were their key metrics at that time?
3. How does this company compare?

Consider recent transactions:
- Funding rounds at similar stages
- M&A transactions in the space
- IPO valuations (adjusted for stage)

Return a JSON object:
{
    "methodology": "Comparable Analysis",
    "comparables_used": [
        {
            "name": "string",
            "transaction_type": "Funding/M&A/IPO",
            "date": "string",
            "valuation": {"amount": "number", "unit": "M/B"},
            "revenue_at_time": {"amount": "number", "unit": "M"},
            "implied_multiple": "number",
            "key_similarities": ["string"],
            "key_differences": ["string"],
            "relevance_score": "number 0-1"
        }
    ],
    "median_multiple": "number",
    "implied_valuation_range": {
        "low": {"amount": "number", "unit": "M"},
        "high": {"amount": "number", "unit": "M"}
    },
    "adjustments_made": ["string - adjustments from comps to target"]
}
"""

DCF_VALUATION_PROMPT = """Perform a simplified DCF valuation.

FINANCIAL DATA:
{financial_data}

ANALYSIS DATA:
{analysis_data}

Build a 5-year projection with:

1. REVENUE PROJECTIONS
   - Base case growth trajectory
   - Revenue in years 1-5

2. MARGIN ASSUMPTIONS
   - Gross margin progression
   - Operating margin at scale
   - Path to profitability

3. TERMINAL VALUE
   - Terminal growth rate (typically 2-4%)
   - Exit multiple approach

4. DISCOUNT RATE
   - Early stage: 30-50%
   - Growth stage: 20-35%
   - Late stage: 15-25%

Return a JSON object:
{
    "methodology": "Discounted Cash Flow",
    "projection_years": 5,
    "projections": [
        {
            "year": "number 1-5",
            "revenue": {"amount": "number", "unit": "M"},
            "growth_rate": "number as decimal",
            "gross_margin": "number as decimal",
            "operating_margin": "number as decimal",
            "fcf": {"amount": "number", "unit": "M"}
        }
    ],
    "terminal_value": {
        "method": "Exit Multiple/Perpetuity Growth",
        "terminal_growth_rate": "number as decimal",
        "exit_multiple": "number (if applicable)",
        "terminal_value": {"amount": "number", "unit": "M"}
    },
    "discount_rate": "number as decimal",
    "discount_rate_rationale": "string",
    "present_value_of_fcf": {"amount": "number", "unit": "M"},
    "present_value_of_terminal": {"amount": "number", "unit": "M"},
    "enterprise_value": {"amount": "number", "unit": "M"},
    "key_assumptions": {
        "revenue_cagr": "number as decimal",
        "terminal_margin": "number as decimal",
        "capex_as_percent_revenue": "number as decimal"
    }
}
"""

SCENARIO_ANALYSIS_PROMPT = """Create bull/base/bear valuation scenarios.

REVENUE MULTIPLE VALUATION:
{revenue_multiple}

COMPARABLE VALUATION:
{comparable_valuation}

DCF VALUATION:
{dcf_valuation}

RISK ASSESSMENT:
{risk_assessment}

Create three scenarios:

1. BULL CASE (20% probability)
   - What goes right?
   - Higher growth, better margins, multiple expansion
   - What's the upside valuation?

2. BASE CASE (60% probability)
   - Most likely outcome
   - Reasonable assumptions
   - Weighted average of methodologies

3. BEAR CASE (20% probability)
   - What goes wrong?
   - Lower growth, compressed multiples, risks materialize
   - What's the downside valuation?

Return a JSON object:
{
    "scenarios": [
        {
            "scenario_name": "Bull/Base/Bear",
            "probability": "number 0-1",
            "valuation": {"amount": "number", "unit": "M"},
            "key_assumptions": ["string"],
            "implied_multiple": "number"
        }
    ],
    "probability_weighted_value": {"amount": "number", "unit": "M"},
    "valuation_range": {
        "low": {"amount": "number", "unit": "M"},
        "mid": {"amount": "number", "unit": "M"},
        "high": {"amount": "number", "unit": "M"}
    }
}
"""

SENSITIVITY_ANALYSIS_PROMPT = """Perform sensitivity analysis on key variables.

BASE VALUATION:
{base_valuation}

KEY ASSUMPTIONS:
{assumptions}

Test sensitivity to:
1. Revenue growth rate (+/- 20%)
2. Gross margin (+/- 5 percentage points)
3. Discount rate (+/- 5 percentage points)
4. Exit multiple (+/- 2x)

For each variable, show how valuation changes.

Return a JSON object:
{
    "sensitivity_analysis": [
        {
            "variable_name": "string",
            "base_value": "number",
            "adjusted_value": "number",
            "resulting_valuation": {"amount": "number", "unit": "M"},
            "change_percentage": "number"
        }
    ],
    "most_sensitive_variable": "string",
    "sensitivity_insights": "string describing key findings"
}
"""

VALUATION_SYNTHESIS_PROMPT = """Synthesize all valuation work into final output.

REVENUE MULTIPLE:
{revenue_multiple}

COMPARABLE ANALYSIS:
{comparable_analysis}

DCF VALUATION:
{dcf_valuation}

SCENARIOS:
{scenarios}

SENSITIVITY:
{sensitivity}

COMPANY ASK:
{company_ask}

Synthesize into final valuation view:

1. RECOMMENDED VALUATION RANGE
   - Low / Mid / High
   - Primary methodology weight

2. COMPARISON TO ASK
   - Is the ask reasonable?
   - Premium or discount implied?

3. INVESTMENT RETURNS
   - What returns are possible?
   - Target ownership and exit scenarios

4. VALUATION RISKS
   - What could make valuation wrong?
   - Key uncertainties

Return a JSON object:
{
    "valuation_range_low": {"amount": "number", "unit": "M"},
    "valuation_range_mid": {"amount": "number", "unit": "M"},
    "valuation_range_high": {"amount": "number", "unit": "M"},
    "probability_weighted_value": {"amount": "number", "unit": "M"},
    "methodologies_used": ["string"],
    "primary_methodology": "string",
    "ask_vs_valuation": "string describing how ask compares",
    "implied_discount_premium": "number (positive = discount, negative = premium)",
    "target_return_multiple": "number (e.g., 3x, 5x, 10x)",
    "target_irr": "number as decimal",
    "valuation_confidence": "high/medium/low",
    "key_valuation_risks": ["string"],
    "recommendation": "string - final view on valuation"
}
"""
