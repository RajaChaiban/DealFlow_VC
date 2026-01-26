"""
Caching service for extraction results.

Caches extraction results by content hash to avoid redundant API calls
for the same document content.
"""

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Optional

from app.utils.logger import logger


class ExtractionCache:
    """
    Simple file-based cache for extraction results.

    Stores results keyed by content hash with TTL (time-to-live) support.
    Uses JSON files in a cache directory for persistence across sessions.

    Attributes:
        cache_dir: Directory to store cache files
        ttl_seconds: Time-to-live for cache entries (default 24 hours)

    Example:
        ```python
        cache = ExtractionCache()

        # Check if result is cached
        result = cache.get(document_content)
        if result is None:
            # Extract and cache
            result = await extract_data(document_content)
            cache.set(document_content, result)
        ```
    """

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        ttl_seconds: int = 86400,  # 24 hours default
    ) -> None:
        """
        Initialize the extraction cache.

        Args:
            cache_dir: Directory to store cache files. Defaults to .cache/extractions
            ttl_seconds: Time-to-live for cache entries in seconds (default 24 hours)
        """
        if cache_dir is None:
            # Use project-relative cache directory
            cache_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                ".cache",
                "extractions"
            )

        self.cache_dir = Path(cache_dir)
        self.ttl_seconds = ttl_seconds

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"ExtractionCache initialized at {self.cache_dir} with TTL={ttl_seconds}s")

    def _compute_hash(self, content: str) -> str:
        """
        Compute SHA-256 hash of content.

        Args:
            content: Content to hash (document text)

        Returns:
            Hex string of content hash
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _get_cache_path(self, content_hash: str) -> Path:
        """
        Get the file path for a cache entry.

        Args:
            content_hash: Hash of the content

        Returns:
            Path to the cache file
        """
        return self.cache_dir / f"{content_hash}.json"

    def get(self, content: str) -> Optional[dict[str, Any]]:
        """
        Retrieve cached extraction result for content.

        Args:
            content: Document content to look up

        Returns:
            Cached extraction result dict, or None if not found or expired
        """
        content_hash = self._compute_hash(content)
        cache_path = self._get_cache_path(content_hash)

        if not cache_path.exists():
            logger.debug(f"Cache miss: {content_hash[:16]}...")
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_entry = json.load(f)

            # Check if expired
            cached_at = cache_entry.get("cached_at", 0)
            age_seconds = time.time() - cached_at

            if age_seconds > self.ttl_seconds:
                logger.debug(
                    f"Cache expired: {content_hash[:16]}... "
                    f"(age={age_seconds:.0f}s, ttl={self.ttl_seconds}s)"
                )
                # Delete expired entry
                cache_path.unlink(missing_ok=True)
                return None

            logger.info(
                f"Cache hit: {content_hash[:16]}... "
                f"(age={age_seconds:.0f}s)"
            )
            return cache_entry.get("data")

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Invalid cache entry {content_hash[:16]}...: {e}")
            # Delete corrupted entry
            cache_path.unlink(missing_ok=True)
            return None

    def set(self, content: str, data: dict[str, Any]) -> None:
        """
        Store extraction result in cache.

        Args:
            content: Document content (used to compute hash key)
            data: Extraction result dict to cache
        """
        content_hash = self._compute_hash(content)
        cache_path = self._get_cache_path(content_hash)

        cache_entry = {
            "cached_at": time.time(),
            "content_hash": content_hash,
            "content_length": len(content),
            "data": data,
        }

        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_entry, f, indent=2, default=str)

            logger.info(f"Cached extraction result: {content_hash[:16]}...")

        except OSError as e:
            logger.warning(f"Failed to cache result: {e}")

    def invalidate(self, content: str) -> bool:
        """
        Remove a specific cache entry.

        Args:
            content: Document content to invalidate

        Returns:
            True if entry was removed, False if not found
        """
        content_hash = self._compute_hash(content)
        cache_path = self._get_cache_path(content_hash)

        if cache_path.exists():
            cache_path.unlink()
            logger.info(f"Invalidated cache entry: {content_hash[:16]}...")
            return True

        return False

    def clear(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Number of entries removed
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1

        logger.info(f"Cleared {count} cache entries")
        return count

    def cleanup_expired(self) -> int:
        """
        Remove all expired cache entries.

        Returns:
            Number of expired entries removed
        """
        count = 0
        current_time = time.time()

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache_entry = json.load(f)

                cached_at = cache_entry.get("cached_at", 0)
                if current_time - cached_at > self.ttl_seconds:
                    cache_file.unlink()
                    count += 1

            except (json.JSONDecodeError, OSError):
                # Remove corrupted files
                cache_file.unlink(missing_ok=True)
                count += 1

        if count > 0:
            logger.info(f"Cleaned up {count} expired cache entries")

        return count

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats (total entries, size, oldest/newest entry)
        """
        entries = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in entries)

        oldest_age = 0
        newest_age = float("inf")
        current_time = time.time()

        for cache_file in entries:
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache_entry = json.load(f)
                age = current_time - cache_entry.get("cached_at", current_time)
                oldest_age = max(oldest_age, age)
                newest_age = min(newest_age, age)
            except (json.JSONDecodeError, OSError):
                pass

        return {
            "total_entries": len(entries),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "oldest_entry_age_hours": round(oldest_age / 3600, 1) if oldest_age > 0 else 0,
            "newest_entry_age_hours": round(newest_age / 3600, 1) if newest_age < float("inf") else 0,
            "ttl_hours": round(self.ttl_seconds / 3600, 1),
        }


# Global cache instance
_extraction_cache: Optional[ExtractionCache] = None


def get_extraction_cache() -> ExtractionCache:
    """
    Get the global extraction cache instance.

    Returns:
        ExtractionCache instance (creates one if needed)
    """
    global _extraction_cache
    if _extraction_cache is None:
        _extraction_cache = ExtractionCache()
    return _extraction_cache
