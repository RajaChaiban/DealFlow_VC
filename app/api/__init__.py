"""
API routers for DealFlow AI Copilot.

This package contains all FastAPI route handlers.
"""

from app.api.deals import router as deals_router
from app.api.health import router as health_router
from app.api.simple_deals import router as simple_deals_router
from app.api.comparison import router as comparison_router
from app.api.export import router as export_router
from app.api.pipeline import router as pipeline_router
from app.api.chat import router as chat_router
from app.api.auth import router as auth_router
from app.api.confidence import router as confidence_router
from app.api.analytics import router as analytics_router

__all__ = [
    "health_router",
    "deals_router",
    "simple_deals_router",
    "comparison_router",
    "export_router",
    "pipeline_router",
    "chat_router",
    "auth_router",
    "confidence_router",
    "analytics_router",
]
