"""
Health check endpoint for DealFlow AI Copilot.

Provides system health status for monitoring and load balancers.
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter

from app import __version__

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Health Check",
    description="Returns the health status of the API",
    response_description="Health status with timestamp and version",
)
async def health_check() -> dict[str, Any]:
    """
    Perform health check.

    Returns:
        Dictionary with health status, timestamp, and version.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": __version__,
        "service": "dealflow-ai-copilot",
    }


@router.get(
    "/health/ready",
    summary="Readiness Check",
    description="Returns whether the service is ready to accept requests",
)
async def readiness_check() -> dict[str, Any]:
    """
    Check if service is ready to accept requests.

    Returns:
        Dictionary with readiness status.
    """
    # TODO: Add checks for external dependencies (DB, cache, etc.)
    return {
        "ready": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get(
    "/health/live",
    summary="Liveness Check",
    description="Returns whether the service is alive",
)
async def liveness_check() -> dict[str, Any]:
    """
    Check if service is alive.

    Returns:
        Dictionary with liveness status.
    """
    return {
        "alive": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
