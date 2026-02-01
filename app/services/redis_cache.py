"""
Redis caching service for DealFlow AI Copilot.

Provides async caching for analysis results, extraction data,
and frequently accessed resources. Falls back gracefully if Redis
is unavailable.
"""

import json
from typing import Any, Optional

import redis.asyncio as aioredis

from app.config import settings
from app.utils.logger import logger


class RedisCacheService:
    """Async Redis cache service with JSON serialization."""

    def __init__(self, redis_url: Optional[str] = None, default_ttl: int = 3600) -> None:
        self.redis_url = redis_url or settings.redis_url
        self.default_ttl = default_ttl
        self._redis: Optional[aioredis.Redis] = None

    async def connect(self) -> None:
        """Establish Redis connection."""
        try:
            self._redis = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                retry_on_timeout=True,
            )
            await self._redis.ping()
            logger.info(f"Redis connected: {self.redis_url}")
        except Exception as e:
            logger.warning(f"Redis connection failed (caching disabled): {e}")
            self._redis = None

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            logger.info("Redis connection closed")

    @property
    def is_connected(self) -> bool:
        return self._redis is not None

    async def get(self, key: str) -> Optional[Any]:
        """Get a cached value by key."""
        if not self._redis:
            return None
        try:
            data = await self._redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.warning(f"Cache get error for '{key}': {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a cached value with optional TTL."""
        if not self._redis:
            return False
        try:
            serialized = json.dumps(value, default=str)
            await self._redis.set(key, serialized, ex=ttl or self.default_ttl)
            return True
        except Exception as e:
            logger.warning(f"Cache set error for '{key}': {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete a cached key."""
        if not self._redis:
            return False
        try:
            await self._redis.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error for '{key}': {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self._redis:
            return False
        try:
            return bool(await self._redis.exists(key))
        except Exception:
            return False

    async def set_analysis_result(self, analysis_id: str, result: dict) -> bool:
        """Cache an analysis result (24h TTL)."""
        return await self.set(f"analysis:{analysis_id}", result, ttl=86400)

    async def get_analysis_result(self, analysis_id: str) -> Optional[dict]:
        """Get a cached analysis result."""
        return await self.get(f"analysis:{analysis_id}")

    async def set_analysis_status(self, analysis_id: str, status: dict) -> bool:
        """Cache analysis status for polling (5min TTL)."""
        return await self.set(f"status:{analysis_id}", status, ttl=300)

    async def get_analysis_status(self, analysis_id: str) -> Optional[dict]:
        """Get cached analysis status."""
        return await self.get(f"status:{analysis_id}")

    async def invalidate_analysis(self, analysis_id: str) -> None:
        """Invalidate all cache entries for an analysis."""
        await self.delete(f"analysis:{analysis_id}")
        await self.delete(f"status:{analysis_id}")

    async def cache_chat_history(self, session_id: str, messages: list[dict]) -> bool:
        """Cache chat history for a session (1h TTL)."""
        return await self.set(f"chat:{session_id}", messages, ttl=3600)

    async def get_chat_history(self, session_id: str) -> Optional[list[dict]]:
        """Get cached chat history."""
        return await self.get(f"chat:{session_id}")

    async def health_check(self) -> dict[str, Any]:
        """Check Redis health."""
        if not self._redis:
            return {"healthy": False, "error": "Not connected"}
        try:
            await self._redis.ping()
            info = await self._redis.info("memory")
            return {
                "healthy": True,
                "used_memory": info.get("used_memory_human", "unknown"),
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}


# Singleton
_redis_cache: Optional[RedisCacheService] = None


def get_redis_cache() -> RedisCacheService:
    """Get the global Redis cache service instance."""
    global _redis_cache
    if _redis_cache is None:
        _redis_cache = RedisCacheService()
    return _redis_cache
