"""
Confidence Heatmap API for DealFlow AI Copilot.

Provides confidence scores for each extracted data point,
allowing analysts to know which numbers to verify.
"""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deals import _analysis_results
from app.utils.logger import logger

router = APIRouter(prefix="/confidence", tags=["confidence-heatmap"])


@router.get(
    "/{analysis_id}",
    summary="Get Confidence Heatmap",
    description="""
Get a confidence heatmap for an analysis, showing extraction confidence
for each data point. Higher confidence = more reliable data.

**Confidence Levels:**
- `high` (0.8-1.0): Data clearly stated in deck, verified across sources
- `medium` (0.5-0.8): Data partially stated or inferred
- `low` (0.0-0.5): Data estimated or missing, needs verification
""",
)
async def get_confidence_heatmap(analysis_id: str) -> dict[str, Any]:
    """Get confidence heatmap for extracted data."""
    memo = _analysis_results.get(analysis_id)
    if not memo:
        raise HTTPException(status_code=404, detail=f"Analysis not found: {analysis_id}")

    extraction = memo.extraction_result
    heatmap = _build_heatmap(extraction.model_dump())

    return {
        "analysis_id": analysis_id,
        "company_name": memo.company_name,
        "overall_extraction_confidence": extraction.extraction_confidence,
        "total_data_points": heatmap["total_points"],
        "high_confidence_count": heatmap["high_count"],
        "medium_confidence_count": heatmap["medium_count"],
        "low_confidence_count": heatmap["low_count"],
        "missing_count": heatmap["missing_count"],
        "categories": heatmap["categories"],
        "data_quality_flags": extraction.data_quality_flags,
        "missing_data_points": extraction.missing_data_points,
    }


def _build_heatmap(extraction: dict) -> dict[str, Any]:
    """Build confidence heatmap from extraction data."""
    categories: dict[str, dict[str, Any]] = {}

    # Company basics
    company_fields = {
        "company_name": extraction.get("company_name"),
        "tagline": extraction.get("tagline"),
        "description": extraction.get("description"),
        "website": extraction.get("website"),
        "founded_year": extraction.get("founded_year"),
        "headquarters": extraction.get("headquarters"),
        "industry": extraction.get("industry"),
        "business_model": extraction.get("business_model"),
        "stage": extraction.get("stage"),
    }
    categories["company_basics"] = _score_fields(company_fields)

    # Financials
    financials = extraction.get("financials", {})
    financial_fields = {
        "revenue": financials.get("revenue"),
        "revenue_growth_rate": financials.get("revenue_growth_rate"),
        "mrr": financials.get("mrr"),
        "arr": financials.get("arr"),
        "gross_margin": financials.get("gross_margin"),
        "net_margin": financials.get("net_margin"),
        "cash_on_hand": financials.get("cash_on_hand"),
        "monthly_burn_rate": financials.get("monthly_burn_rate"),
        "runway_months": financials.get("runway_months"),
        "total_raised": financials.get("total_raised"),
        "pre_money_valuation": financials.get("pre_money_valuation"),
    }
    categories["financials"] = _score_fields(financial_fields)

    # Unit economics
    ue = extraction.get("unit_economics", {})
    ue_fields = {
        "cac": ue.get("cac"),
        "ltv": ue.get("ltv"),
        "ltv_cac_ratio": ue.get("ltv_cac_ratio"),
        "payback_period_months": ue.get("payback_period_months"),
        "net_revenue_retention": ue.get("net_revenue_retention"),
        "churn_rate": ue.get("churn_rate"),
        "arpu": ue.get("arpu"),
    }
    categories["unit_economics"] = _score_fields(ue_fields)

    # Market data
    market = extraction.get("market", {})
    market_fields = {
        "tam": market.get("tam"),
        "sam": market.get("sam"),
        "som": market.get("som"),
        "market_growth_rate": market.get("market_growth_rate"),
        "market_description": market.get("market_description"),
    }
    categories["market"] = _score_fields(market_fields)

    # Team
    team = extraction.get("team", {})
    team_fields = {
        "founders": team.get("founders") if team.get("founders") else None,
        "total_employees": team.get("total_employees"),
        "employee_growth_rate": team.get("employee_growth_rate"),
    }
    categories["team"] = _score_fields(team_fields)

    # Traction
    traction = extraction.get("traction", {})
    traction_fields = {
        "total_customers": traction.get("total_customers"),
        "customer_growth_rate": traction.get("customer_growth_rate"),
        "total_users": traction.get("total_users"),
        "mau": traction.get("mau"),
        "engagement_rate": traction.get("engagement_rate"),
    }
    categories["traction"] = _score_fields(traction_fields)

    # Aggregate counts
    total_points = 0
    high_count = 0
    medium_count = 0
    low_count = 0
    missing_count = 0

    for cat_name, cat_data in categories.items():
        for field in cat_data.get("fields", {}).values():
            total_points += 1
            level = field.get("confidence_level", "missing")
            if level == "high":
                high_count += 1
            elif level == "medium":
                medium_count += 1
            elif level == "low":
                low_count += 1
            else:
                missing_count += 1

    return {
        "categories": categories,
        "total_points": total_points,
        "high_count": high_count,
        "medium_count": medium_count,
        "low_count": low_count,
        "missing_count": missing_count,
    }


def _score_fields(fields: dict[str, Any]) -> dict[str, Any]:
    """Score confidence for a set of fields."""
    scored_fields = {}
    total_score = 0
    count = 0

    for name, value in fields.items():
        if value is None:
            scored_fields[name] = {
                "value": None,
                "confidence_score": 0.0,
                "confidence_level": "missing",
                "needs_verification": True,
            }
        elif isinstance(value, dict):
            # MonetaryValue or nested object
            has_amount = value.get("amount") is not None and value.get("amount") != 0
            scored_fields[name] = {
                "value": value,
                "confidence_score": 0.8 if has_amount else 0.3,
                "confidence_level": "high" if has_amount else "low",
                "needs_verification": not has_amount,
            }
            total_score += 0.8 if has_amount else 0.3
        elif isinstance(value, (list,)):
            has_data = len(value) > 0
            scored_fields[name] = {
                "value": f"{len(value)} items",
                "confidence_score": 0.7 if has_data else 0.2,
                "confidence_level": "medium" if has_data else "low",
                "needs_verification": not has_data,
            }
            total_score += 0.7 if has_data else 0.2
        else:
            scored_fields[name] = {
                "value": value,
                "confidence_score": 0.9,
                "confidence_level": "high",
                "needs_verification": False,
            }
            total_score += 0.9

        count += 1

    category_score = total_score / count if count > 0 else 0

    return {
        "category_score": round(category_score, 2),
        "field_count": count,
        "fields": scored_fields,
    }
