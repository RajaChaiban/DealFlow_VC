"""
API routers for DealFlow AI Copilot.

This package contains all FastAPI route handlers.
"""

from app.api.deals import router as deals_router
from app.api.health import router as health_router

__all__ = ["health_router", "deals_router"]
