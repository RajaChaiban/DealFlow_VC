"""
Shared pytest fixtures for DealFlow AI Copilot test suite.

Provides:
- Async HTTP client for API testing (httpx.AsyncClient)
- In-memory SQLite test database
- Mock Gemini client
- Sample data fixtures
"""

import asyncio
from datetime import datetime
from typing import Any, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database.models import Base


# ---------------------------------------------------------------------------
# Event loop configuration
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# Test Database
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def test_engine():
    """Create an in-memory SQLite async engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a test database session."""
    TestSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with TestSessionLocal() as session:
        yield session


# ---------------------------------------------------------------------------
# Application & Client Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def async_client(test_engine) -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP client bound to the FastAPI test application.

    Uses an in-memory SQLite database for all DB-dependent endpoints.
    """
    TestSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with TestSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    # Import modules before patching so they are registered in their parent packages
    import app.main  # noqa: F401
    import app.services.redis_cache  # noqa: F401

    with (
        patch("app.main.settings") as mock_settings,
        patch("app.services.redis_cache.get_redis_cache", return_value=MagicMock()),
        patch("app.database.session.init_db", new_callable=AsyncMock),
        patch("app.database.session.close_db", new_callable=AsyncMock),
    ):
        mock_settings.app_name = "DealFlow AI Copilot"
        mock_settings.debug = False
        mock_settings.default_model = "gemini-1.5-pro-latest"
        mock_settings.cors_origin_list = ["*"]
        mock_settings.redis_url = ""
        mock_settings.rate_limit_per_minute = 1000
        mock_settings.rate_limit_per_hour = 10000
        mock_settings.jwt_secret_key = "test-secret-key-for-testing"
        mock_settings.jwt_algorithm = "HS256"
        mock_settings.jwt_access_token_expire_minutes = 60
        mock_settings.api_keys = ""
        mock_settings.google_api_key = "test-api-key"
        mock_settings.default_temperature = 0.3
        mock_settings.get_data_directories.return_value = []

        from app.main import app
        from app.database.session import get_db

        # Override the get_db dependency with our test database
        app.dependency_overrides[get_db] = override_get_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            yield client

        # Clean up the override and module-level state
        app.dependency_overrides.pop(get_db, None)

        # Clear in-memory stores that persist across tests
        from app.api.deals import _analysis_jobs, _analysis_results
        _analysis_jobs.clear()
        _analysis_results.clear()


# ---------------------------------------------------------------------------
# Mock Gemini Client
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_gemini_client() -> MagicMock:
    """
    Mock GeminiClient that returns canned responses.

    Use this to avoid hitting the real Gemini API during tests.
    """
    client = MagicMock()
    client.generate = AsyncMock(return_value="Mock AI response text.")
    client.generate_structured = AsyncMock(
        return_value={
            "response": "This is a mock structured response.",
            "sources": ["Mock source"],
            "suggested_questions": ["What is the revenue?"],
        }
    )
    client.analyze_with_vision = AsyncMock(return_value="Mock vision analysis.")
    client.count_tokens = AsyncMock(return_value=42)
    client.health_check = AsyncMock(
        return_value={"healthy": True, "latency_ms": 100, "model": "gemini-1.5-flash-latest"}
    )
    return client


# ---------------------------------------------------------------------------
# Sample Data Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_monetary_value() -> dict[str, Any]:
    """Sample MonetaryValue data."""
    return {"amount": 5.0, "currency": "USD", "unit": "M"}


@pytest.fixture
def sample_extraction_result() -> dict[str, Any]:
    """
    Sample ExtractionResult as a dictionary, matching the Pydantic schema.

    Represents a realistic pitch deck extraction for a SaaS company.
    """
    return {
        "company_name": "TechVenture AI",
        "tagline": "AI-powered sales intelligence platform",
        "description": "TechVenture AI automates sales research and outbound workflows.",
        "website": "https://techventure.ai",
        "founded_year": 2021,
        "headquarters": "San Francisco, CA",
        "industry": "Enterprise Software",
        "sector": "AI/ML",
        "business_model": "SaaS",
        "stage": "series_a",
        "team": {
            "founders": [
                {
                    "name": "Jane Smith",
                    "title": "CEO",
                    "background": "Ex-Google, Stanford CS",
                    "previous_companies": ["Google", "Stripe"],
                    "education": "Stanford CS PhD",
                    "years_experience": 12,
                }
            ],
            "total_employees": 45,
            "employee_growth_rate": 150.0,
            "key_hires": ["VP Engineering from Salesforce"],
            "open_roles": ["Sr. ML Engineer", "Head of Sales"],
            "team_gaps": ["No CFO"],
        },
        "financials": {
            "revenue": {"amount": 3.2, "currency": "USD", "unit": "M"},
            "revenue_growth_rate": 180.0,
            "arr": {"amount": 3.2, "currency": "USD", "unit": "M"},
            "gross_margin": 0.82,
            "monthly_burn_rate": {"amount": 250, "currency": "USD", "unit": "K"},
            "runway_months": 18,
            "total_raised": {"amount": 8, "currency": "USD", "unit": "M"},
            "current_round_size": {"amount": 15, "currency": "USD", "unit": "M"},
            "pre_money_valuation": {"amount": 60, "currency": "USD", "unit": "M"},
        },
        "unit_economics": {
            "cac": {"amount": 5000, "currency": "USD", "unit": ""},
            "ltv": {"amount": 45000, "currency": "USD", "unit": ""},
            "ltv_cac_ratio": 9.0,
            "payback_period_months": 6,
            "net_revenue_retention": 1.25,
            "churn_rate": 0.02,
        },
        "market": {
            "tam": {"amount": 50, "currency": "USD", "unit": "B"},
            "sam": {"amount": 12, "currency": "USD", "unit": "B"},
            "som": {"amount": 800, "currency": "USD", "unit": "M"},
            "market_growth_rate": 25.0,
        },
        "traction": {
            "total_customers": 120,
            "customer_growth_rate": 200.0,
            "enterprise_customers": 15,
            "notable_customers": ["Acme Corp", "BigTech Inc"],
            "total_users": 5000,
            "mau": 3500,
        },
        "competitors": [
            {"name": "CompetitorA", "description": "Established player"},
            {"name": "CompetitorB", "description": "Well-funded startup"},
        ],
        "competitive_advantages": ["Proprietary AI model", "10x faster data processing"],
        "product_description": "AI sales intelligence platform",
        "key_features": ["Lead scoring", "Auto-research", "CRM integration"],
        "technology_stack": ["Python", "React", "GCP"],
        "funding_ask": {"amount": 15, "currency": "USD", "unit": "M"},
        "use_of_funds": [
            {"category": "Engineering", "percentage": 40},
            {"category": "Sales & Marketing", "percentage": 35},
            {"category": "Operations", "percentage": 25},
        ],
        "extraction_confidence": 0.87,
        "data_quality_flags": [],
        "missing_data_points": ["net_margin"],
        "source_page_count": 24,
    }


@pytest.fixture
def sample_analysis_result() -> dict[str, Any]:
    """
    Sample AnalysisResult as a dictionary, matching the Pydantic schema.

    Represents a realistic AI-generated deal analysis output.
    """
    confidence_score = {
        "score": 7.5,
        "confidence": "high",
        "reasoning": "Strong fundamentals with clear growth trajectory.",
    }
    medium_score = {
        "score": 6.0,
        "confidence": "medium",
        "reasoning": "Moderate strength with some concerns.",
    }

    return {
        "business_model": {
            "overall_score": confidence_score,
            "revenue_quality": confidence_score,
            "margin_structure": confidence_score,
            "scalability": {"score": 8.0, "confidence": "high", "reasoning": "SaaS scales well."},
            "defensibility": medium_score,
            "capital_efficiency": confidence_score,
        },
        "market_analysis": {
            "market_score": confidence_score,
            "tam_validity": medium_score,
            "market_timing": confidence_score,
            "market_dynamics": "Growing demand for AI in sales tech.",
            "tailwinds": ["AI adoption wave", "Remote sales growth"],
            "headwinds": ["Enterprise budget cuts", "Regulatory uncertainty"],
        },
        "competitive_analysis": {
            "competitive_score": confidence_score,
            "market_position": "Challenger",
            "differentiation_strength": confidence_score,
            "barriers_to_entry": medium_score,
            "competitive_threats": ["Well-funded incumbents"],
            "sustainable_advantages": ["Proprietary data moat"],
        },
        "growth_analysis": {
            "growth_score": {"score": 8.5, "confidence": "high", "reasoning": "180% YoY growth."},
            "historical_growth_rate": 180.0,
            "projected_growth_rate": 120.0,
            "growth_drivers": ["Enterprise expansion", "New product lines"],
            "growth_constraints": ["Hiring pace", "Market education"],
            "growth_sustainability": confidence_score,
        },
        "unit_economics_quality": confidence_score,
        "team_assessment": confidence_score,
        "investment_thesis": {
            "thesis_statement": (
                "TechVenture AI is well-positioned to capture a significant share of the "
                "AI sales intelligence market given its proprietary technology and strong "
                "early traction with enterprise customers."
            ),
            "key_beliefs": [
                "AI will transform B2B sales processes",
                "First-mover advantage in data moat is sustainable",
            ],
            "upside_drivers": ["Land-and-expand in enterprise", "Platform play"],
            "key_concerns": ["Competition from incumbents", "Long enterprise sales cycles"],
            "thesis_confidence": "high",
        },
        "comparable_companies": [
            {
                "name": "Gong.io",
                "similarity_score": 0.8,
                "outcome": "Private ($7.2B valuation)",
                "key_similarities": ["AI sales tool", "Enterprise focus"],
                "key_differences": ["Conversation intelligence vs. research"],
            },
        ],
        "overall_attractiveness_score": {
            "score": 7.8,
            "confidence": "high",
            "reasoning": "Strong team, product-market fit, and growth metrics.",
        },
        "key_strengths": ["Exceptional growth rate", "Strong unit economics"],
        "key_weaknesses": ["Limited brand awareness", "No CFO"],
        "critical_questions": ["Path to profitability?", "Enterprise pipeline depth?"],
        "analysis_confidence": 0.85,
    }


@pytest.fixture
def sample_risk_result() -> dict[str, Any]:
    """Sample RiskResult data for testing."""
    return {
        "risks": [
            {
                "id": "R001",
                "title": "Customer concentration risk",
                "description": "Top 3 customers represent 40% of revenue.",
                "category": "financial",
                "severity": "high",
                "likelihood": "medium",
                "impact": "Revenue volatility if a major customer churns.",
                "mitigation": "Diversify customer base with SMB segment.",
                "evidence": ["Revenue breakdown shows concentration"],
                "affected_areas": ["revenue", "growth"],
            }
        ],
        "risk_summaries": [],
        "consistency_checks": [],
        "data_integrity_score": 0.9,
        "overall_risk_score": 5.5,
        "risk_adjusted_recommendation": "invest",
        "recommendation_reasoning": "Risks are manageable with proper mitigation.",
        "deal_breakers": [],
        "must_verify_items": ["Customer contracts"],
        "total_risks": 1,
        "critical_risks": 0,
        "high_risks": 1,
        "assessment_confidence": 0.82,
    }


# ---------------------------------------------------------------------------
# Auth Helper Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def test_user_data() -> dict[str, str]:
    """Standard test user registration data."""
    return {
        "email": "testuser@dealflow.ai",
        "password": "SecurePass123!",
        "full_name": "Test User",
        "organization": "Test Fund LP",
    }


@pytest.fixture
def test_login_data() -> dict[str, str]:
    """Standard test user login data."""
    return {
        "email": "testuser@dealflow.ai",
        "password": "SecurePass123!",
    }
