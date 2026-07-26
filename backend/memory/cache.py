"""
MemoryCache — Phase 3.6 Production Hardening

TTL-based query result cache for the memory system.

Caches the results of ``retrieve_memory`` calls to avoid re-embedding
identical queries within a configurable time window.  The cache is
keyed on (project_id, collection_name, query_text, limit, threshold).

Features
--------
- TTL expiry (default 5 minutes)
- LRU eviction when ``max_size`` is reached
- Per-key invalidation
- Project-scoped invalidation (invalidate_project)
- Hit/miss statistics

Usage
-----
    cache = MemoryCache(ttl_seconds=300, max_size=256)

    results = cache.get(project_id=1, collection="requirements", query="auth")
    if results is None:
        results = expensive_retrieve(...)
        cache.set(project_id=1, collection="requirements", query="auth", results=results)

    # After writing new memory, invalidate that project's cache:
    cache.invalidate_project(project_id=1)
"""
from __future__ import annotations

import hashlib
import logging
import time
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_DEFAULT_TTL     = 300   # seconds
_DEFAULT_MAX_SIZE = 256  # entries


def _cache_key(
    project_id: int,
    collection_name: str,
    query: str,
    limit: int,
    threshold: float,
) -> str:
    """Build a stable, compact cache key."""
    raw = f"{project_id}:{collection_name}:{query}:{limit}:{threshold:.4f}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


class _CacheEntry:
    __slots__ = ("value", "expires_at", "project_id")

    def __init__(self, value: Any, ttl: float, project_id: int) -> None:
        self.value = value
        self.expires_at = time.monotonic() + ttl
        self.project_id = project_id

    def is_expired(self) -> bool:
        return time.monotonic() >= self.expires_at


class MemoryCache:
    """
    TTL + LRU cache for memory query results.

    Args:
        ttl_seconds: How long (in seconds) a cached entry stays valid.
        max_size:    Maximum number of entries before LRU eviction.
    """

    def __init__(
        self,
        ttl_seconds: float = _DEFAULT_TTL,
        max_size: int = _DEFAULT_MAX_SIZE,
    ) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self._store: OrderedDict[str, _CacheEntry] = OrderedDict()
        self._hits = 0
        self._misses = 0

    # ------------------------------------------------------------------
    # Core get / set
    # ------------------------------------------------------------------

    def get(
        self,
        project_id: int,
        collection_name: str,
        query: str,
        limit: int = 5,
        threshold: float = 0.0,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Return cached results or ``None`` if not cached / expired.
        """
        key = _cache_key(project_id, collection_name, query, limit, threshold)
        entry = self._store.get(key)
        if entry is None:
            self._misses += 1
            return None
        if entry.is_expired():
            del self._store[key]
            self._misses += 1
            return None
        # Move to end (most recently used)
        self._store.move_to_end(key)
        self._hits += 1
        return entry.value

    def set(
        self,
        project_id: int,
        collection_name: str,
        query: str,
        results: List[Dict[str, Any]],
        limit: int = 5,
        threshold: float = 0.0,
    ) -> None:
        """Store query results in the cache."""
        key = _cache_key(project_id, collection_name, query, limit, threshold)
        # Evict LRU entry if at capacity
        if len(self._store) >= self.max_size and key not in self._store:
            self._store.popitem(last=False)
        self._store[key] = _CacheEntry(results, self.ttl_seconds, project_id)
        self._store.move_to_end(key)
        logger.debug(
            "[CACHE] Stored key=%s (project=%d, col=%s)",
            key[:8], project_id, collection_name,
        )

    # ------------------------------------------------------------------
    # Invalidation
    # ------------------------------------------------------------------

    def invalidate(
        self,
        project_id: int,
        collection_name: str,
        query: str,
        limit: int = 5,
        threshold: float = 0.0,
    ) -> bool:
        """Remove a specific entry. Returns True if it existed."""
        key = _cache_key(project_id, collection_name, query, limit, threshold)
        if key in self._store:
            del self._store[key]
            return True
        return False

    def invalidate_project(self, project_id: int) -> int:
        """
        Remove all cached entries for *project_id*.

        Returns:
            Number of entries removed.
        """
        keys_to_remove = [
            k for k, v in self._store.items()
            if v.project_id == project_id
        ]
        for k in keys_to_remove:
            del self._store[k]
        if keys_to_remove:
            logger.debug(
                "[CACHE] Invalidated %d entries for project %d",
                len(keys_to_remove), project_id,
            )
        return len(keys_to_remove)

    def clear(self) -> None:
        """Wipe the entire cache."""
        self._store.clear()
        logger.debug("[CACHE] Cache cleared")

    # ------------------------------------------------------------------
    # Maintenance — evict expired entries
    # ------------------------------------------------------------------

    def evict_expired(self) -> int:
        """
        Remove all entries whose TTL has elapsed.

        Returns:
            Number of entries evicted.
        """
        expired = [k for k, v in self._store.items() if v.is_expired()]
        for k in expired:
            del self._store[k]
        return len(expired)

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    @property
    def size(self) -> int:
        """Current number of entries (including potentially expired ones)."""
        return len(self._store)

    @property
    def hits(self) -> int:
        return self._hits

    @property
    def misses(self) -> int:
        return self._misses

    @property
    def hit_rate(self) -> float:
        """Cache hit rate as a fraction [0.0 – 1.0]."""
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    def stats(self) -> Dict[str, Any]:
        """Return a snapshot of cache statistics."""
        return {
            "size": self.size,
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self.hit_rate, 4),
        }
