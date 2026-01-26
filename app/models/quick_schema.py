"""
Simplified extraction schemas for fast, reliable extraction.

These schemas focus on essential fields only to avoid timeouts and improve reliability.
"""

from typing import Any

# Quick extraction schema - ~15 essential fields
# This should complete in 5-15 seconds vs 60+ seconds for full schema
QUICK_EXTRACTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "company_name": {"type": "string", "description": "Company name"},
        "tagline": {"type": ["string", "null"], "description": "Company tagline or one-liner"},
        "industry": {"type": ["string", "null"], "description": "Primary industry"},
        "stage": {
            "type": ["string", "null"],
            "enum": ["pre_seed", "seed", "series_a", "series_b", "series_c", "growth", "late_stage", None],
            "description": "Funding stage"
        },
        "business_model": {
            "type": ["string", "null"],
            "enum": ["saas", "marketplace", "d2c", "hardware", "services", "fintech", "other", None],
            "description": "Business model type"
        },
        "revenue_arr_millions": {"type": ["number", "null"], "description": "Annual recurring revenue in millions USD"},
        "growth_rate_percent": {"type": ["number", "null"], "description": "Year-over-year growth rate as percentage (e.g., 150 for 150%)"},
        "gross_margin_percent": {"type": ["number", "null"], "description": "Gross margin as percentage"},
        "burn_rate_millions": {"type": ["number", "null"], "description": "Monthly burn rate in millions USD"},
        "runway_months": {"type": ["number", "null"], "description": "Months of runway remaining"},
        "total_raised_millions": {"type": ["number", "null"], "description": "Total funding raised to date in millions USD"},
        "asking_amount_millions": {"type": ["number", "null"], "description": "Current round ask in millions USD"},
        "pre_money_valuation_millions": {"type": ["number", "null"], "description": "Pre-money valuation in millions USD"},
        "tam_billions": {"type": ["number", "null"], "description": "Total addressable market in billions USD"},
        "total_customers": {"type": ["number", "null"], "description": "Number of customers"},
        "team_size": {"type": ["number", "null"], "description": "Number of employees"},
        "founder_names": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of founder names"
        },
        "headquarters": {"type": ["string", "null"], "description": "HQ location"},
        "founded_year": {"type": ["number", "null"], "description": "Year founded"},
    },
    "required": ["company_name"]
}

# Detailed financials schema - for phase 2
DETAILED_FINANCIALS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "mrr_thousands": {"type": ["number", "null"]},
        "arr_millions": {"type": ["number", "null"]},
        "revenue_growth_yoy": {"type": ["number", "null"]},
        "gross_margin": {"type": ["number", "null"]},
        "net_margin": {"type": ["number", "null"]},
        "ebitda_millions": {"type": ["number", "null"]},
        "cash_on_hand_millions": {"type": ["number", "null"]},
        "monthly_burn_millions": {"type": ["number", "null"]},
        "cac_dollars": {"type": ["number", "null"]},
        "ltv_dollars": {"type": ["number", "null"]},
        "ltv_cac_ratio": {"type": ["number", "null"]},
        "payback_months": {"type": ["number", "null"]},
        "nrr_percent": {"type": ["number", "null"]},
        "churn_percent": {"type": ["number", "null"]},
    }
}

# Detailed team schema - for phase 2
DETAILED_TEAM_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "founders": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "title": {"type": ["string", "null"]},
                    "background": {"type": ["string", "null"]},
                    "previous_companies": {"type": "array", "items": {"type": "string"}}
                }
            }
        },
        "total_employees": {"type": ["number", "null"]},
        "engineering_size": {"type": ["number", "null"]},
        "sales_size": {"type": ["number", "null"]},
        "key_hires": {"type": "array", "items": {"type": "string"}},
        "open_roles": {"type": "array", "items": {"type": "string"}},
        "team_gaps": {"type": "array", "items": {"type": "string"}}
    }
}

# Detailed market schema - for phase 2
DETAILED_MARKET_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "tam_billions": {"type": ["number", "null"]},
        "sam_billions": {"type": ["number", "null"]},
        "som_millions": {"type": ["number", "null"]},
        "market_growth_rate": {"type": ["number", "null"]},
        "market_description": {"type": ["string", "null"]},
        "competitors": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": ["string", "null"]},
                    "funding_millions": {"type": ["number", "null"]}
                }
            }
        },
        "competitive_advantages": {"type": "array", "items": {"type": "string"}},
        "notable_customers": {"type": "array", "items": {"type": "string"}}
    }
}


# Quick extraction prompt - simplified for speed
QUICK_EXTRACTION_PROMPT = """Extract the essential company information from this pitch deck.

Focus on finding these key data points:
- Company name and basic info (industry, stage, location, founded year)
- Key financials (revenue/ARR, growth rate, margins, burn rate, runway)
- Funding info (total raised, current ask, valuation)
- Market size (TAM)
- Team basics (founder names, team size, customer count)

Be precise with numbers. Use null for any data not found.
Do not guess or estimate - only extract explicitly stated values.

PITCH DECK CONTENT:
{content}

Return a JSON object with the extracted data.
"""

DETAILED_FINANCIALS_PROMPT = """Extract detailed financial metrics from this content.

Focus on:
- Revenue metrics (MRR, ARR, growth rates)
- Profitability (margins, EBITDA)
- Cash position (burn rate, runway, cash on hand)
- Unit economics (CAC, LTV, LTV/CAC ratio, payback period)
- Retention metrics (NRR, churn)

CONTENT:
{content}

Return a JSON object with the financial data. Use null for missing values.
"""

DETAILED_TEAM_PROMPT = """Extract detailed team information from this content.

Focus on:
- Founder details (names, titles, backgrounds, previous companies)
- Team composition (total size, by function)
- Recent key hires
- Open roles being hired for
- Any apparent team gaps

CONTENT:
{content}

Return a JSON object with the team data.
"""

DETAILED_MARKET_PROMPT = """Extract detailed market and competitive information from this content.

Focus on:
- Market sizing (TAM, SAM, SOM with sources if mentioned)
- Market growth rate
- Named competitors and their funding/position
- Company's competitive advantages
- Notable customers or logos

CONTENT:
{content}

Return a JSON object with the market data.
"""
