"""
DealFlow AI Copilot - FastAPI Application

Main entry point for the DealFlow AI Copilot API.
Provides AI-powered private equity deal analysis with multi-agent orchestration.

Architecture:
- Orchestrator Agent: Coordinates the analysis pipeline
- Extraction Agent: Extracts data from pitch decks (vision + text)
- Analysis Agent: Business model, market, and competitive analysis
- Risk Agent: Comprehensive risk assessment
- Valuation Agent: Multi-methodology valuation

Target: Complete IC memo generation in 30-60 seconds.
"""

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api import (
    analytics_router,
    auth_router,
    chat_router,
    comparison_router,
    confidence_router,
    deals_router,
    export_router,
    health_router,
    pipeline_router,
    simple_deals_router,
)
from app.config import settings
from app.middleware.auth import AuthMiddleware
from app.middleware.rate_limit import setup_rate_limiting
from app.utils import logger
from app.utils.exceptions import (
    AnalysisError,
    APIError,
    DealFlowBaseException,
    ExtractionError,
    ValidationError,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events including database and cache initialization.
    """
    # Startup
    logger.info("Starting DealFlow AI Copilot...")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Default model: {settings.default_model}")

    # Create data directories
    for directory in settings.get_data_directories():
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {directory}")

    # Initialize Redis cache (non-blocking, falls back gracefully)
    try:
        from app.services.redis_cache import get_redis_cache
        cache = get_redis_cache()
        await cache.connect()
    except Exception as e:
        logger.warning(f"Redis not available (caching disabled): {e}")

    # Initialize database (optional, only if PostgreSQL is available)
    try:
        from app.database.session import init_db
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"Database not available (using in-memory storage): {e}")

    logger.info("DealFlow AI Copilot started successfully")

    yield

    # Shutdown
    logger.info("Shutting down DealFlow AI Copilot...")

    # Close Redis
    try:
        from app.services.redis_cache import get_redis_cache
        cache = get_redis_cache()
        await cache.disconnect()
    except Exception:
        pass

    # Close database
    try:
        from app.database.session import close_db
        await close_db()
    except Exception:
        pass


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
## DealFlow AI Copilot

AI-powered private equity deal analysis platform with multi-agent orchestration using Google Gemini.

### Features
- **Deal Analysis**: Upload pitch decks for automated IC memo generation
- **Deal Comparison**: Compare 2-3 deals side-by-side
- **Deal Pipeline**: Kanban-style deal tracking and management
- **Chat Analysis**: Conversational follow-up questions about deals
- **Export**: Download memos as PDF, DOCX, or JSON
- **Confidence Heatmap**: See extraction confidence per data point

### Multi-Agent Architecture
```
Orchestrator ─┬─> Extraction Agent (PDF → Structured Data)
              ├─> Analysis Agent (Business/Market/Competitive)
              ├─> Risk Agent (Financial/Team/Market Risks)
              └─> Valuation Agent (Multiple Methodologies)
```

### Authentication
- **JWT Bearer Tokens**: For user sessions (`Authorization: Bearer <token>`)
- **API Keys**: For programmatic access (`X-API-Key: <key>`)

### API Sections
- **Auth**: User registration, login, API key management
- **Health**: System health and readiness checks
- **Deals**: Deal analysis (upload, analyze, results)
- **Compare**: Side-by-side deal comparison
- **Pipeline**: Kanban deal tracking
- **Chat**: Conversational deal analysis
- **Export**: PDF/DOCX/JSON export
- **Confidence**: Data confidence heatmap
    """,
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth Middleware (logging only, doesn't block)
app.add_middleware(AuthMiddleware)

# Rate Limiting
setup_rate_limiting(app)


# Exception handler for custom exceptions
@app.exception_handler(DealFlowBaseException)
async def dealflow_exception_handler(
    request: Request, exc: DealFlowBaseException
) -> JSONResponse:
    """Handle DealFlow custom exceptions."""
    logger.error(f"DealFlow error: {exc.message}", extra={"details": exc.details})
    return JSONResponse(
        status_code=500,
        content=exc.to_dict(),
    )


# Include routers
app.include_router(health_router)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(deals_router, prefix="/api/v1")
app.include_router(simple_deals_router, prefix="/api/v1")
app.include_router(comparison_router, prefix="/api/v1")
app.include_router(export_router, prefix="/api/v1")
app.include_router(pipeline_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(confidence_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")


@app.get(
    "/",
    summary="Root",
    description="Returns basic information about the API",
    tags=["root"],
)
async def root() -> dict[str, Any]:
    """
    Root endpoint with API information.

    Returns:
        Dictionary with API name, version, and documentation URLs.
    """
    return {
        "name": settings.app_name,
        "version": __version__,
        "description": "AI-powered private equity deal analysis platform",
        "features": [
            "Multi-agent deal analysis",
            "Deal comparison",
            "Pipeline management",
            "Conversational analysis",
            "PDF/DOCX export",
            "Confidence heatmap",
            "JWT & API key authentication",
            "Rate limiting",
        ],
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
        },
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )
