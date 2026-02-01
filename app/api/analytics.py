"""
Portfolio analytics endpoints for DealFlow AI Copilot.

Provides aggregate metrics across all deals and pipeline data.
"""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import DealAnalysis, DealPipelineEntry
from app.database.session import get_db
from app.database import crud

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get(
    "/portfolio",
    summary="Portfolio Analytics",
    description="Aggregate analytics across all deals: score distribution, recommendations, sectors, pipeline stats.",
)
async def get_portfolio_analytics(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return portfolio-wide analytics."""

    # --- Score distribution (buckets 0-2, 2-4, 4-6, 6-8, 8-10) ---
    analyses_result = await db.execute(
        select(DealAnalysis).where(DealAnalysis.status == "completed")
    )
    analyses = list(analyses_result.scalars().all())

    score_buckets = {"0-2": 0, "2-4": 0, "4-6": 0, "6-8": 0, "8-10": 0}
    recommendation_counts: dict[str, int] = {}
    industry_counts: dict[str, int] = {}
    scores: list[float] = []

    for a in analyses:
        # Score distribution
        score = a.overall_attractiveness_score
        if score is not None:
            scores.append(score)
            if score < 2:
                score_buckets["0-2"] += 1
            elif score < 4:
                score_buckets["2-4"] += 1
            elif score < 6:
                score_buckets["4-6"] += 1
            elif score < 8:
                score_buckets["6-8"] += 1
            else:
                score_buckets["8-10"] += 1

        # Recommendation breakdown
        rec = a.recommendation or "Unknown"
        recommendation_counts[rec] = recommendation_counts.get(rec, 0) + 1

        # Industry breakdown
        industry = a.industry or "Unknown"
        industry_counts[industry] = industry_counts.get(industry, 0) + 1

    avg_score = round(sum(scores) / len(scores), 1) if scores else 0
    total_completed = len(analyses)

    # --- Pipeline stats from crud ---
    pipeline_stats = await crud.get_pipeline_stats(db)

    # --- Monthly deal volume (last 6 months) ---
    monthly_volume: dict[str, int] = {}
    for a in analyses:
        if a.created_at:
            key = a.created_at.strftime("%Y-%m")
            monthly_volume[key] = monthly_volume.get(key, 0) + 1

    # Sort monthly volume by date and take last 6
    sorted_months = sorted(monthly_volume.items())[-6:]

    return {
        "total_deals_analyzed": total_completed,
        "average_score": avg_score,
        "score_distribution": score_buckets,
        "recommendation_breakdown": recommendation_counts,
        "industry_breakdown": industry_counts,
        "pipeline": pipeline_stats,
        "monthly_volume": [
            {"month": m, "count": c} for m, c in sorted_months
        ],
    }
