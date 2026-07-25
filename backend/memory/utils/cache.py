"""
Embedding LRU cache — wraps any EmbeddingProviderInterface and caches
results in-process to avoid redundant calls to Ollama / HuggingFace API.

Usage
-----
    from memory.utils.cache import CachedEmbeddingProvider
    from memory.embeddings import resolve_provider

    raw_provider = resolve_provider()
    provider = CachedEmbeddingProvider(raw_provider, max_size=512)
"""
from __future__ import annotations

import hashlib
import logging
from functools import lru_cache
from typing import List

from memory.interfaces.embedding import EmbeddingProviderInterface

logger = logging.getLogger(__name__)


def _text_key(text: str) -> str:
    """Stable hash key for a text string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class CachedEmbeddingProvider(EmbeddingProviderInterface):
    """
    Transparent caching wrapper for any EmbeddingProviderInterface.

    Embedding calls are deduplicated using an in-process LRU cache keyed
    on a SHA-256 hash of the input text.  Thread-safe for read-heavy
    workloads (Python's GIL protects the dict operations).

    Args:
        provider:  Underlying embedding provider to wrap.
        max_size:  Maximum number of cached embeddings.
    """

    def __init__(self, provider: EmbeddingProviderInterface, max_size: int = 512) -> None:
        self._provider = provider
        self._max_size = max_size
        self._cache: dict[str, List[float]] = {}
        self._hits = 0
        self._misses = 0

    # ------------------------------------------------------------------
    # EmbeddingProviderInterface — delegation with caching
    # ------------------------------------------------------------------

    @property
    def dimension(self) -> int:
        return self._provider.dimension

    @property
    def provider_name(self) -> str:
        return f"cached({self._provider.provider_name})"

    def health_check(self) -> bool:
        return self._provider.health_check()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        results: List[List[float]] = []
        texts_to_embed: List[str] = []
        indices_to_fill: List[int] = []

        # Populate from cache where possible
        temp: List[List[float] | None] = []
        for text in texts:
            key = _text_key(text)
            if key in self._cache:
                self._hits += 1
                temp.append(self._cache[key])
            else:
                self._misses += 1
                indices_to_fill.append(len(temp))
                texts_to_embed.append(text)
                temp.append(None)

        # Embed cache misses
        if texts_to_embed:
            fresh = self._provider.embed_documents(texts_to_embed)
            for idx, (text, vec) in zip(indices_to_fill, zip(texts_to_embed, fresh)):
                # Evict oldest if at capacity (simple FIFO overflow guard)
                if len(self._cache) >= self._max_size:
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]
                self._cache[_text_key(text)] = vec
                temp[idx] = vec

        results = [v for v in temp if v is not None]
        logger.debug(
            "[CACHE] embed_documents: %d hits, %d misses (cache size=%d)",
            self._hits,
            self._misses,
            len(self._cache),
        )
        return results

    def embed_query(self, text: str) -> List[float]:
        key = _text_key(text)
        if key in self._cache:
            self._hits += 1
            logger.debug("[CACHE] embed_query HIT")
            return self._cache[key]

        self._misses += 1
        vec = self._provider.embed_query(text)
        if len(self._cache) >= self._max_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        self._cache[key] = vec
        return vec

    # ------------------------------------------------------------------
    # Cache management
    # ------------------------------------------------------------------

    def clear_cache(self) -> None:
        """Evict all cached embeddings."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    @property
    def cache_stats(self) -> dict:
        return {
            "hits": self._hits,
            "misses": self._misses,
            "size": len(self._cache),
            "max_size": self._max_size,
        }
