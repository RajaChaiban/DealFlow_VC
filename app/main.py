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
from app.api import deals_router, health_router
from app.config import settings
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

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting DealFlow AI Copilot...")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Default model: {settings.default_model}")

    # Create data directories
    for directory in settings.get_data_directories():
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {directory}")

    logger.info("DealFlow AI Copilot started successfully")

    yield

    # Shutdown
    logger.info("Shutting down DealFlow AI Copilot...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
## DealFlow AI Copilot

AI-powered private equity deal analysis platform with multi-agent orchestration using Google Gemini.

### What It Does
Upload a pitch deck PDF and receive a complete Investment Committee memo in 30-60 seconds, including:
- **Data Extraction**: Financial metrics, team info, market data from unstructured documents
- **Business Analysis**: Model viability, market opportunity, competitive positioning
- **Risk Assessment**: Systematic red flag identification with severity scoring
- **Valuation**: Revenue multiples, comparables, DCF with scenario analysis
- **IC Memo**: Professional investment memorandum ready for review

### Multi-Agent Architecture
```
Orchestrator ─┬─> Extraction Agent (PDF → Structured Data)
              │
              ├─> Analysis Agent (Business/Market/Competitive)
              │
              ├─> Risk Agent (Financial/Team/Market Risks)
              │
              └─> Valuation Agent (Multiple Methodologies)
```

### API Workflow
1. `POST /api/v1/deals/upload` - Upload pitch deck PDF
2. `POST /api/v1/deals/analyze` - Start background analysis
3. `GET /api/v1/deals/{id}/status` - Check progress
4. `GET /api/v1/deals/{id}/result` - Get complete IC memo

Or use `POST /api/v1/deals/analyze/sync` for synchronous analysis (blocks until complete).

### API Sections
- **Health**: System health and readiness checks
- **Deals**: Deal document upload, analysis, and results
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
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
app.include_router(deals_router, prefix="/api/v1")


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
