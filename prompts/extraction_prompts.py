"""
Prompt templates for the Extraction Agent.

These prompts guide Gemini in extracting structured data from pitch decks,
handling both text and visual content (charts, tables, graphics).
"""

EXTRACTION_SYSTEM_PROMPT = """You are an expert private equity analyst at a top-tier firm like Goldman Sachs or KKR.
Your task is to extract structured financial and company data from pitch deck presentations.

You have exceptional attention to detail and can:
- Parse financial tables and charts accurately
- Identify key metrics even when presented inconsistently
- Flag data quality issues and inconsistencies
- Handle various pitch deck formats and styles

Always extract data conservatively - if a number is unclear, flag it rather than guess.
Maintain professional skepticism about claimed metrics.
"""

EXTRACTION_MAIN_PROMPT = """Analyze this pitch deck and extract all relevant company and financial data.

EXTRACTION GUIDELINES:
1. Extract ALL numerical data you can find - revenue, growth rates, customer counts, etc.
2. For financial figures, always note:
   - The exact value and unit (K, M, B)
   - The time period (FY2023, Q1 2024, LTM, etc.)
   - Whether it's actual vs. projected
3. For percentages, confirm the base they're calculated from
4. Extract team information including backgrounds, previous companies, and notable achievements
5. Identify the business model type (SaaS, Marketplace, D2C, Hardware, etc.)
6. Note any data inconsistencies or red flags

REQUIRED OUTPUT STRUCTURE:
Return a JSON object with the following structure:

{
    "company_name": "string",
    "tagline": "string or null",
    "description": "string or null",
    "website": "string or null",
    "founded_year": "number or null",
    "headquarters": "string or null",
    "industry": "string or null",
    "sector": "string or null",
    "business_model": "string (SaaS/Marketplace/D2C/Hardware/Services/Other)",
    "stage": "string (pre_seed/seed/series_a/series_b/series_c/growth/late_stage)",

    "team": {
        "founders": [
            {
                "name": "string",
                "title": "string",
                "background": "string or null",
                "previous_companies": ["string"],
                "education": "string or null"
            }
        ],
        "total_employees": "number or null",
        "employee_growth_rate": "number or null (as decimal, e.g., 0.50 for 50%)",
        "key_hires": ["string"],
        "open_roles": ["string"],
        "team_gaps": ["string"]
    },

    "financials": {
        "revenue": {"amount": "number", "currency": "USD", "unit": "M/K/B"},
        "revenue_growth_rate": "number or null (as decimal)",
        "mrr": {"amount": "number", "currency": "USD", "unit": "M/K"},
        "arr": {"amount": "number", "currency": "USD", "unit": "M/K"},
        "gross_margin": "number or null (as decimal)",
        "net_margin": "number or null (as decimal)",
        "ebitda": {"amount": "number", "currency": "USD", "unit": "M/K"},
        "ebitda_margin": "number or null (as decimal)",
        "cash_on_hand": {"amount": "number", "currency": "USD", "unit": "M/K"},
        "monthly_burn_rate": {"amount": "number", "currency": "USD", "unit": "M/K"},
        "runway_months": "number or null",
        "total_raised": {"amount": "number", "currency": "USD", "unit": "M/K"},
        "current_round_size": {"amount": "number", "currency": "USD", "unit": "M/K"},
        "pre_money_valuation": {"amount": "number", "currency": "USD", "unit": "M/K"},
        "revenue_history": [
            {"period": "string", "revenue": "number", "unit": "M/K"}
        ]
    },

    "unit_economics": {
        "cac": {"amount": "number", "currency": "USD", "unit": ""},
        "ltv": {"amount": "number", "currency": "USD", "unit": ""},
        "ltv_cac_ratio": "number or null",
        "payback_period_months": "number or null",
        "arpu": {"amount": "number", "currency": "USD", "unit": ""},
        "net_revenue_retention": "number or null (as decimal, e.g., 1.20 for 120%)",
        "gross_revenue_retention": "number or null (as decimal)",
        "churn_rate": "number or null (as decimal, monthly)"
    },

    "market": {
        "tam": {"amount": "number", "currency": "USD", "unit": "B/M"},
        "sam": {"amount": "number", "currency": "USD", "unit": "B/M"},
        "som": {"amount": "number", "currency": "USD", "unit": "B/M"},
        "tam_source": "string or null",
        "market_growth_rate": "number or null (as decimal)",
        "market_description": "string or null"
    },

    "traction": {
        "total_customers": "number or null",
        "customer_growth_rate": "number or null (as decimal)",
        "enterprise_customers": "number or null",
        "smb_customers": "number or null",
        "notable_customers": ["string"],
        "total_users": "number or null",
        "mau": "number or null",
        "dau": "number or null",
        "user_growth_rate": "number or null (as decimal)",
        "engagement_rate": "number or null (as decimal)",
        "conversion_rate": "number or null (as decimal)",
        "gmv": {"amount": "number", "currency": "USD", "unit": "M/K"}
    },

    "competitors": [
        {
            "name": "string",
            "description": "string or null",
            "funding_raised": {"amount": "number", "currency": "USD", "unit": "M"},
            "market_position": "string or null",
            "key_differentiators": ["string"]
        }
    ],

    "competitive_advantages": ["string"],

    "product_description": "string or null",
    "key_features": ["string"],
    "technology_stack": ["string"],

    "funding_ask": {"amount": "number", "currency": "USD", "unit": "M"},
    "use_of_funds": [
        {"category": "string", "percentage": "number", "description": "string"}
    ],

    "extraction_confidence": "number (0-1, your confidence in extraction quality)",
    "data_quality_flags": ["string (issues found in data)"],
    "missing_data_points": ["string (important data not found)"]
}

IMPORTANT:
- Use null for any field where data is not found or unclear
- All percentages should be decimals (50% = 0.50)
- Flag any inconsistencies in data_quality_flags
- List important missing data in missing_data_points
- Be conservative - don't infer numbers that aren't explicitly stated

Now analyze the pitch deck content provided and extract all data:
"""

VISION_EXTRACTION_PROMPT = """Analyze these pitch deck slides and extract all visible data.

Pay special attention to:
1. CHARTS AND GRAPHS: Extract exact values, labels, and trends
2. TABLES: Capture all rows and columns with their values
3. FINANCIAL METRICS: Revenue, growth rates, margins, unit economics
4. LOGOS: Company logos may indicate notable customers or partners
5. TEAM PHOTOS: Note names and titles from team slides
6. SCREENSHOTS: Product screenshots may show features and metrics

For each chart/table you see:
- Describe what it shows
- Extract all data points you can read
- Note the time period covered
- Flag if values are hard to read

Remember: Extract what you SEE, don't infer or estimate unclear values.
"""

FINANCIAL_VALIDATION_PROMPT = """Review the extracted financial data and validate internal consistency.

Check for:
1. Revenue math: Does MRR x 12 ≈ ARR?
2. Growth consistency: Do historical data points support claimed growth rates?
3. Unit economics: Does CAC + payback period align with LTV claims?
4. Burn rate vs runway: Does cash ÷ burn ≈ stated runway?
5. Round size vs use of funds: Do percentages add up?
6. Margin consistency: Gross margin > Net margin?

For each inconsistency found, explain:
- What values conflict
- What the expected relationship should be
- Severity (critical/high/medium/low)

Return a list of validation results.
"""
