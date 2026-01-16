"""
Prompt templates for the Analysis Agent.

These prompts guide deep business evaluation across multiple dimensions:
business model, market opportunity, competitive positioning, and growth trajectory.
"""

ANALYSIS_SYSTEM_PROMPT = """You are a senior investment professional at a top-tier private equity firm.
You have 15+ years of experience evaluating companies across technology, healthcare, and consumer sectors.

Your analysis style is:
- Rigorous and data-driven
- Skeptical of management claims without evidence
- Focused on unit economics and business model sustainability
- Experienced in pattern recognition from hundreds of deals
- Clear about conviction level and key uncertainties

You think like an owner, not just an analyst. You ask: "Would I put my own money into this?"
"""

BUSINESS_MODEL_ANALYSIS_PROMPT = """Analyze the business model of this company based on the extracted data.

COMPANY DATA:
{extraction_data}

Evaluate each dimension on a 0-10 scale with reasoning:

1. REVENUE QUALITY (0-10)
   - Is revenue recurring or one-time?
   - How predictable is the revenue stream?
   - Are there long-term contracts or month-to-month?
   - What's the revenue concentration risk?

2. MARGIN STRUCTURE (0-10)
   - What are gross margins and how do they compare to peers?
   - Is there a clear path to profitability?
   - Are margins improving or declining?
   - What's the underlying cost structure?

3. SCALABILITY (0-10)
   - Can the business grow without proportional cost increases?
   - What's the incremental margin on new revenue?
   - Are there operational bottlenecks?
   - How capital-intensive is growth?

4. DEFENSIBILITY (0-10)
   - What competitive moats exist?
   - Network effects, switching costs, brand, IP?
   - How easy is it for competitors to replicate?
   - Is there customer lock-in?

5. CAPITAL EFFICIENCY (0-10)
   - How much capital is needed to generate revenue?
   - What's the CAC payback period?
   - Is the company efficiently deploying capital?
   - Burn multiple (burn / net new ARR)?

Return a JSON object:
{
    "overall_score": {
        "score": "number 0-10",
        "confidence": "high/medium/low",
        "reasoning": "string"
    },
    "revenue_quality": {
        "score": "number 0-10",
        "confidence": "high/medium/low",
        "reasoning": "string"
    },
    "margin_structure": {
        "score": "number 0-10",
        "confidence": "high/medium/low",
        "reasoning": "string"
    },
    "scalability": {
        "score": "number 0-10",
        "confidence": "high/medium/low",
        "reasoning": "string"
    },
    "defensibility": {
        "score": "number 0-10",
        "confidence": "high/medium/low",
        "reasoning": "string"
    },
    "capital_efficiency": {
        "score": "number 0-10",
        "confidence": "high/medium/low",
        "reasoning": "string"
    }
}
"""

MARKET_ANALYSIS_PROMPT = """Evaluate the market opportunity for this company.

COMPANY DATA:
{extraction_data}

Analyze:

1. TAM/SAM/SOM VALIDITY
   - Are the market size claims believable?
   - What's the source and methodology?
   - Is the market definition too broad or appropriately scoped?
   - How does this compare to third-party estimates?

2. MARKET TIMING
   - Is this the right time for this solution?
   - What secular trends support this market?
   - Is the market emerging, growing, or mature?
   - Are there regulatory or technology tailwinds?

3. MARKET DYNAMICS
   - Is the market growing or shrinking?
   - What's driving market growth?
   - Are there market-specific risks?
   - Winner-take-all vs. fragmented?

Return a JSON object:
{
    "market_score": {
        "score": "number 0-10",
        "confidence": "high/medium/low",
        "reasoning": "string"
    },
    "tam_validity": {
        "score": "number 0-10",
        "confidence": "high/medium/low",
        "reasoning": "string"
    },
    "market_timing": {
        "score": "number 0-10",
        "confidence": "high/medium/low",
        "reasoning": "string"
    },
    "market_dynamics": "string describing key market forces",
    "tailwinds": ["string - factors helping the market"],
    "headwinds": ["string - factors hurting the market"]
}
"""

COMPETITIVE_ANALYSIS_PROMPT = """Assess the competitive positioning of this company.

COMPANY DATA:
{extraction_data}

Analyze:

1. MARKET POSITION
   - Is this company a leader, challenger, or niche player?
   - What's their share of the target market?
   - How do they rank vs. competitors?

2. DIFFERENTIATION STRENGTH
   - What makes this company different?
   - Is the differentiation sustainable?
   - Do customers care about these differences?

3. BARRIERS TO ENTRY
   - How hard is it for new entrants to compete?
   - What would it cost to replicate this business?
   - Are there regulatory or technical barriers?

4. COMPETITIVE THREATS
   - Who are the main competitors?
   - What are incumbents doing?
   - Are there well-funded startups in the space?
   - Could big tech enter this market?

Return a JSON object:
{
    "competitive_score": {
        "score": "number 0-10",
        "confidence": "high/medium/low",
        "reasoning": "string"
    },
    "market_position": "leader/challenger/niche/emerging",
    "differentiation_strength": {
        "score": "number 0-10",
        "confidence": "high/medium/low",
        "reasoning": "string"
    },
    "barriers_to_entry": {
        "score": "number 0-10",
        "confidence": "high/medium/low",
        "reasoning": "string"
    },
    "competitive_threats": ["string - specific threats"],
    "sustainable_advantages": ["string - lasting advantages"]
}
"""

GROWTH_ANALYSIS_PROMPT = """Analyze the growth trajectory and sustainability.

COMPANY DATA:
{extraction_data}

Evaluate:

1. HISTORICAL GROWTH
   - What has been the actual growth rate?
   - Is growth accelerating or decelerating?
   - What drove historical growth?

2. GROWTH SUSTAINABILITY
   - Can current growth rates continue?
   - What's needed to maintain growth?
   - Are there natural growth limiters?

3. GROWTH DRIVERS
   - What levers exist for future growth?
   - New products, markets, or segments?
   - Pricing power?

4. GROWTH CONSTRAINTS
   - What could slow growth?
   - Market saturation?
   - Competitive pressure?
   - Operational limitations?

Return a JSON object:
{
    "growth_score": {
        "score": "number 0-10",
        "confidence": "high/medium/low",
        "reasoning": "string"
    },
    "historical_growth_rate": "number as decimal",
    "projected_growth_rate": "number as decimal (your estimate)",
    "growth_drivers": ["string"],
    "growth_constraints": ["string"],
    "growth_sustainability": {
        "score": "number 0-10",
        "confidence": "high/medium/low",
        "reasoning": "string"
    }
}
"""

INVESTMENT_THESIS_PROMPT = """Synthesize all analysis into an investment thesis.

COMPANY DATA:
{extraction_data}

BUSINESS MODEL ANALYSIS:
{business_model_analysis}

MARKET ANALYSIS:
{market_analysis}

COMPETITIVE ANALYSIS:
{competitive_analysis}

GROWTH ANALYSIS:
{growth_analysis}

Create a compelling investment thesis that addresses:

1. THE CORE THESIS
   - In one paragraph, why should we invest in this company?
   - What's the primary value creation opportunity?

2. KEY BELIEFS
   - What must be true for this investment to succeed?
   - List 3-5 critical assumptions

3. UPSIDE DRIVERS
   - What could make this better than expected?
   - Potential positive surprises?

4. KEY CONCERNS
   - What worries you most?
   - What could go wrong?

5. COMPARABLE COMPANIES
   - What successful companies does this remind you of?
   - At what stage and valuation?

Return a JSON object:
{
    "investment_thesis": {
        "thesis_statement": "string - one paragraph thesis",
        "key_beliefs": ["string - what must be true"],
        "upside_drivers": ["string"],
        "key_concerns": ["string"],
        "thesis_confidence": "high/medium/low"
    },
    "comparable_companies": [
        {
            "name": "string",
            "similarity_score": "number 0-1",
            "outcome": "string (IPO/Acquired/Private/Failed)",
            "valuation_at_similar_stage": {"amount": "number", "unit": "M/B"},
            "key_similarities": ["string"],
            "key_differences": ["string"]
        }
    ],
    "overall_attractiveness_score": {
        "score": "number 0-10",
        "confidence": "high/medium/low",
        "reasoning": "string"
    },
    "key_strengths": ["string"],
    "key_weaknesses": ["string"],
    "critical_questions": ["string - questions for management"]
}
"""

TEAM_ASSESSMENT_PROMPT = """Evaluate the founding team and organization.

TEAM DATA:
{team_data}

Assess:

1. FOUNDER QUALITY
   - Relevant experience for this business?
   - Track record of success?
   - Domain expertise?
   - Complementary skills?

2. TEAM COMPLETENESS
   - Are key roles filled?
   - Any critical gaps?
   - Quality of recent hires?

3. EXECUTION CAPABILITY
   - Evidence of execution ability?
   - Have they built and scaled before?
   - Can they attract talent?

Return a JSON object:
{
    "team_score": {
        "score": "number 0-10",
        "confidence": "high/medium/low",
        "reasoning": "string"
    },
    "founder_assessment": "string - overall founder evaluation",
    "team_gaps": ["string - missing roles or skills"],
    "team_strengths": ["string"],
    "concerns": ["string"]
}
"""
