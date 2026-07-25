"""
MemoryManager — provider registry and lifecycle manager.

Responsibilities:
    - Hold the active embedding provider and vector store instances.
    - Expose health-check and provider-switching logic.
    - Act as the single wiring point for the MemoryService.

Usage
-----
    from memory.manager import MemoryManager

    manager = MemoryManager()          # auto-selects providers from env
    service = manager.get_service()    # returns a ready MemoryService
"""
from __future__ import annotations

import logging
from typing import Optional

from memory.config import settings
from memory.interfaces import EmbeddingProviderInterface, VectorStoreInterface
from memory.schemas import ProviderHealth

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Central wiring and lifecycle manager for the memory subsystem.

    Args:
        embedding_provider: Override the embedding provider.  When ``None``
                            the provider is resolved from env-vars using the
                            fallback chain.
        vector_store:       Override the vector store backend.  When ``None``
                            a ChromaVectorStore is created using the path
                            from ``memory.config.settings``.
        enable_cache:       Wrap the embedding provider with the in-process
                            LRU cache.  Defaults to the config value.
    """

    def __init__(
        self,
        embedding_provider: Optional[EmbeddingProviderInterface] = None,
        vector_store: Optional[VectorStoreInterface] = None,
        enable_cache: Optional[bool] = None,
    ) -> None:
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store
        self._use_cache = (
            enable_cache
            if enable_cache is not None
            else settings.EMBEDDING_CACHE_ENABLED
        )
        self._service: Optional["MemoryService"] = None  # lazy
        logger.info(
            "[MANAGER] MemoryManager created (provider=%s, cache=%s)",
            embedding_provider.provider_name if embedding_provider else "auto",
            self._use_cache,
        )

    # ------------------------------------------------------------------
    # Provider accessors (lazy-initialised)
    # ------------------------------------------------------------------

    def get_embedding_provider(self) -> EmbeddingProviderInterface:
        """Return the active embedding provider, building it if needed."""
        if self._embedding_provider is None:
            self._embedding_provider = self._build_embedding_provider()
        return self._embedding_provider

    def get_vector_store(self) -> VectorStoreInterface:
        """Return the active vector store, building it if needed."""
        if self._vector_store is None:
            self._vector_store = self._build_vector_store()
        return self._vector_store

    def get_service(self) -> "MemoryService":
        """
        Return a fully-wired :class:`MemoryService` instance.

        The service is built once and cached on the manager instance.
        """
        if self._service is None:
            from memory.service import MemoryService  # avoid circular import

            self._service = MemoryService(
                embedding_provider=self.get_embedding_provider(),
                vector_store=self.get_vector_store(),
            )
        return self._service

    # ------------------------------------------------------------------
    # Provider switching
    # ------------------------------------------------------------------

    def switch_embedding_provider(
        self, new_provider: EmbeddingProviderInterface
    ) -> None:
        """
        Hot-swap the embedding provider at runtime.

        The cached service is invalidated so the next call to
        ``get_service()`` rebuilds with the new provider.
        """
        logger.info(
            "[MANAGER] Switching embedding provider: %s → %s",
            self._embedding_provider.provider_name
            if self._embedding_provider
            else "none",
            new_provider.provider_name,
        )
        self._embedding_provider = new_provider
        self._service = None  # force rebuild

    # ------------------------------------------------------------------
    # Health checks
    # ------------------------------------------------------------------

    def health_check(self) -> ProviderHealth:
        """Run a liveness probe against the active embedding provider."""
        provider = self.get_embedding_provider()
        try:
            healthy = provider.health_check()
            return ProviderHealth(
                provider_name=provider.provider_name,
                healthy=healthy,
                dimension=provider.dimension,
            )
        except Exception as exc:
            return ProviderHealth(
                provider_name=provider.provider_name,
                healthy=False,
                error=str(exc),
            )

    # ------------------------------------------------------------------
    # Internal builders
    # ------------------------------------------------------------------

    def _build_embedding_provider(self) -> EmbeddingProviderInterface:
        from memory.embeddings.resolver import resolve_provider  # avoid circular
        from memory.utils.cache import CachedEmbeddingProvider

        raw = resolve_provider(
            preferred=settings.EMBEDDING_PROVIDER,
            fallback_chain=settings.get_fallback_chain(),
        )

        if self._use_cache:
            logger.info(
                "[MANAGER] Wrapping '%s' with CachedEmbeddingProvider (max=%d)",
                raw.provider_name,
                settings.EMBEDDING_CACHE_MAX_SIZE,
            )
            return CachedEmbeddingProvider(raw, max_size=settings.EMBEDDING_CACHE_MAX_SIZE)

        return raw

    def _build_vector_store(self) -> VectorStoreInterface:
        from memory.vectorstores.chroma import ChromaVectorStore  # avoid circular

        return ChromaVectorStore(persist_path=settings.CHROMA_PERSIST_PATH)


# ---------------------------------------------------------------------------
# Module-level default manager instance
# ---------------------------------------------------------------------------
# Import this singleton where you need a manager but don't need custom wiring:
#
#     from memory.manager import default_manager
#     service = default_manager.get_service()
#
default_manager = MemoryManager()
