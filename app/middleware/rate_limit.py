"""
Rate limiting middleware for DealFlow AI Copilot.

Uses slowapi to enforce per-client rate limits on API endpoints.
"""

from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.utils.logger import logger


def _get_identifier(request: Request) -> str:
    """
    Get rate limit identifier from request.

    Prioritizes API key, then Bearer token subject, then IP address.
    """
    # Check API key first
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"apikey:{api_key[:8]}"

    # Check Bearer token
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        return f"bearer:{auth[7:15]}"

    # Fall back to IP
    return get_remote_address(request)


# Create limiter instance — fall back to in-memory storage when Redis is unavailable
try:
    limiter = Limiter(
        key_func=_get_identifier,
        default_limits=[
            f"{settings.rate_limit_per_minute}/minute",
            f"{settings.rate_limit_per_hour}/hour",
        ],
        storage_uri=settings.redis_url if settings.redis_url else "memory://",
    )
except Exception:
    logger.warning("Redis unavailable for rate limiting, using in-memory storage")
    limiter = Limiter(
        key_func=_get_identifier,
        default_limits=[
            f"{settings.rate_limit_per_minute}/minute",
            f"{settings.rate_limit_per_hour}/hour",
        ],
        storage_uri="memory://",
    )


def setup_rate_limiting(app: FastAPI) -> None:
    """
    Configure rate limiting on the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    logger.info(
        f"Rate limiting configured: {settings.rate_limit_per_minute}/min, "
        f"{settings.rate_limit_per_hour}/hour"
    )
