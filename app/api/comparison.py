"""
Deal Comparison API for DealFlow AI Copilot.

Compare 2-3 deals side-by-side with ranked recommendations.
"""

from typing import Any, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.agents.simple_orchestrator import get_simple_orchestrator
from app.core.gemini_client import get_gemini_client
from app.utils.logger import logger

router = APIRouter(prefix="/compare", tags=["deal-comparison"])


@router.post(
    "/",
    summary="Compare Multiple Deals",
    description="""
Upload 2-3 pitch decks to get a side-by-side comparison with ranked recommendations.

**Output includes:**
- Side-by-side metrics comparison table
- Strengths/weaknesses for each deal
- Risk comparison matrix
- Valuation comparison
- Ranked recommendation with rationale
""",
)
async def compare_deals(
    files: list[UploadFile] = File(
        ..., description="2-3 pitch deck PDFs to compare"
    ),
) -> dict[str, Any]:
    """
    Compare multiple deals side-by-side.

    Runs independent analysis on each deal, then generates a comparative summary.
    """
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="At least 2 files required for comparison")
    if len(files) > 3:
        raise HTTPException(status_code=400, detail="Maximum 3 files for comparison")

    logger.info(f"Starting deal comparison with {len(files)} deals")

    # Analyze each deal independently
    analyses = []
    for file in files:
        content = await file.read()
        filename = file.filename or "unknown.pdf"

        try:
            orchestrator = get_simple_orchestrator()
            result = await orchestrator.analyze_bytes([(filename, content)])
            analyses.append({
                "filename": filename,
                "company_name": result.summary.company_name,
                "result": result.model_dump(),
            })
        except Exception as e:
            logger.error(f"Failed to analyze {filename}: {e}")
            analyses.append({
                "filename": filename,
                "company_name": filename,
                "error": str(e),
            })

    # Generate comparative analysis using Gemini
    successful = [a for a in analyses if "error" not in a]

    if len(successful) < 2:
        raise HTTPException(
            status_code=500,
            detail="Need at least 2 successful analyses for comparison",
        )

    comparison = await _generate_comparison(successful)

    return {
        "deals_analyzed": len(analyses),
        "deals": [
            {
                "filename": a["filename"],
                "company_name": a.get("company_name", "Unknown"),
                "status": "success" if "error" not in a else "failed",
                "error": a.get("error"),
            }
            for a in analyses
        ],
        "comparison": comparison,
        "individual_results": [a["result"] for a in successful],
    }


async def _generate_comparison(analyses: list[dict]) -> dict[str, Any]:
    """Generate a comparative analysis using Gemini."""
    client = get_gemini_client()

    # Build comparison data
    deals_summary = []
    for a in analyses:
        result = a["result"]
        summary = result.get("summary", {})
        extraction = result.get("extraction", {})
        risks = result.get("risks", {})
        valuation = result.get("valuation", {})

        deals_summary.append({
            "company": summary.get("company_name", a["filename"]),
            "recommendation": summary.get("recommendation", "unknown"),
            "overall_score": summary.get("overall_score", 0),
            "financials": extraction.get("financials", {}),
            "risk_score": risks.get("overall_risk_score", 0),
            "risk_count": risks.get("total_risks", 0),
            "valuation_range": {
                "low": valuation.get("valuation_range_low", 0),
                "mid": valuation.get("valuation_range_mid", 0),
                "high": valuation.get("valuation_range_high", 0),
            },
        })

    import json
    deals_json = json.dumps(deals_summary, indent=2, default=str)

    prompt = f"""You are a senior private equity analyst comparing investment opportunities.

Given these deal analyses, provide a structured comparison:

{deals_json}

Generate a JSON response with this structure:
{{
    "ranking": [
        {{
            "rank": 1,
            "company": "Company Name",
            "score": 8.5,
            "rationale": "Why this deal ranks here"
        }}
    ],
    "metrics_comparison": {{
        "revenue": {{"deal_1": "value", "deal_2": "value"}},
        "growth_rate": {{"deal_1": "value", "deal_2": "value"}},
        "risk_score": {{"deal_1": "value", "deal_2": "value"}},
        "valuation": {{"deal_1": "value", "deal_2": "value"}}
    }},
    "strengths_weaknesses": [
        {{
            "company": "Company Name",
            "strengths": ["strength1", "strength2"],
            "weaknesses": ["weakness1", "weakness2"]
        }}
    ],
    "recommendation_summary": "Overall comparative recommendation paragraph",
    "key_differentiators": ["What makes each deal unique"],
    "winner": "Company Name",
    "winner_rationale": "Why this deal is the best opportunity"
}}"""

    result = await client.generate_structured(
        prompt=prompt,
        response_schema={
            "type": "object",
            "properties": {
                "ranking": {"type": "array"},
                "metrics_comparison": {"type": "object"},
                "strengths_weaknesses": {"type": "array"},
                "recommendation_summary": {"type": "string"},
                "key_differentiators": {"type": "array"},
                "winner": {"type": "string"},
                "winner_rationale": {"type": "string"},
            },
        },
        model="pro",
        temperature=0.3,
    )

    return result
