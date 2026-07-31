"""
RetrievalService — Phase 5.2

Semantic retrieval from ChromaDB collections.

Operations:
    search()               — Multi-collection semantic search
    find_similar()         — Single-collection similarity search
    get_project_documents() — Raw document listing for a collection
    get_provider_health()  — Active embedding provider health probe
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from rag.config import rag_settings
from rag.schemas.retrieval import (
    CollectionsResponse,
    DocumentRecord,
    HealthResponse,
    ProjectDocumentsResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
    SimilarityRequest,
    SimilarityResponse,
    SimilarityResult,
)

logger = logging.getLogger(__name__)


class RetrievalService:
    """
    Semantic retrieval service for the RAG pipeline.

    Args:
        memory_service: Optional injected MemoryService for testing.
                        When None, resolved from ``memory.manager.default_manager``.
    """

    def __init__(self, memory_service=None) -> None:
        self._memory_service = memory_service

    # ── Private helpers ─────────────────────────────────────────────────

    def _get_service(self):
        if self._memory_service is not None:
            return self._memory_service
        from memory.manager import default_manager
        return default_manager.get_service()

    def _resolve_collections(self, collections: Optional[List[str]]) -> List[str]:
        """Return the collection list, defaulting to all semantic collections."""
        if collections:
            # Validate against known collections
            known = set(rag_settings.get_collections())
            valid = [c for c in collections if c in known]
            if not valid:
                logger.warning(
                    "[RAG-RETRIEVAL] None of the requested collections are known: %s. "
                    "Defaulting to all semantic collections.",
                    collections,
                )
                return rag_settings.get_search_collections()
            return valid
        return rag_settings.get_search_collections()

    # ── Public API ───────────────────────────────────────────────────────

    async def search(self, request: SearchRequest) -> SearchResponse:
        """
        Perform semantic search across one or more collections.

        Embeds the query once, then queries each collection individually.
        Results from all collections are merged and globally sorted by
        descending similarity score.

        Args:
            request: Validated SearchRequest.

        Returns:
            SearchResponse with merged, ranked results.
        """
        svc = self._get_service()
        collections = self._resolve_collections(request.collections)
        all_results: List[SearchResult] = []

        logger.info(
            "[RAG-RETRIEVAL] Search project=%d query='%s' collections=%s limit=%d threshold=%.2f",
            request.project_id,
            request.query[:80],
            collections,
            request.limit,
            request.threshold,
        )

        for col in collections:
            try:
                raw = svc.retrieve_memory(
                    project_id=request.project_id,
                    collection_name=col,
                    query=request.query,
                    limit=request.limit,
                    threshold=request.threshold,
                )
                for item in raw:
                    all_results.append(
                        SearchResult(
                            id=item["id"],
                            document=item["document"],
                            metadata=item.get("metadata", {}),
                            similarity_score=item["similarity_score"],
                            collection=col,
                        )
                    )
            except Exception as exc:
                logger.warning(
                    "[RAG-RETRIEVAL] Collection '%s' search failed: %s", col, exc
                )

        # Global sort by similarity, deduplicate by document id
        seen_ids: set = set()
        unique: List[SearchResult] = []
        for r in sorted(all_results, key=lambda x: x.similarity_score, reverse=True):
            if r.id not in seen_ids:
                seen_ids.add(r.id)
                unique.append(r)

        # Apply global limit (each collection already applied per-collection limit)
        final = unique[: request.limit * len(collections)]

        logger.info(
            "[RAG-RETRIEVAL] Returned %d merged result(s) from %d collection(s)",
            len(final),
            len(collections),
        )

        return SearchResponse(
            project_id=request.project_id,
            query=request.query,
            results=final,
            total=len(final),
            collections_searched=collections,
        )

    async def find_similar(self, request: SimilarityRequest) -> SimilarityResponse:
        """
        Similarity search within a single named collection.

        Args:
            request: Validated SimilarityRequest.

        Returns:
            SimilarityResponse with ranked results from the target collection.
        """
        svc = self._get_service()

        logger.info(
            "[RAG-RETRIEVAL] Similarity project=%d col=%s query='%s' limit=%d",
            request.project_id,
            request.collection,
            request.query[:80],
            request.limit,
        )

        try:
            raw = svc.retrieve_memory(
                project_id=request.project_id,
                collection_name=request.collection,
                query=request.query,
                limit=request.limit,
                threshold=request.threshold,
            )
        except Exception as exc:
            logger.error(
                "[RAG-RETRIEVAL] find_similar failed for collection '%s': %s",
                request.collection,
                exc,
            )
            raw = []

        results = [
            SimilarityResult(
                id=item["id"],
                document=item["document"],
                metadata=item.get("metadata", {}),
                similarity_score=item["similarity_score"],
                collection=request.collection,
            )
            for item in raw
        ]

        return SimilarityResponse(
            project_id=request.project_id,
            query=request.query,
            collection=request.collection,
            results=results,
            total=len(results),
        )

    async def get_project_documents(
        self,
        project_id: int,
        collection: str,
    ) -> ProjectDocumentsResponse:
        """
        List all raw documents stored for a project in a given collection.

        Args:
            project_id: Owning project.
            collection: Target collection name.

        Returns:
            ProjectDocumentsResponse with all raw document records.
        """
        svc = self._get_service()

        try:
            raw = svc.get_project_memory(project_id, collection)
        except Exception as exc:
            logger.error(
                "[RAG-RETRIEVAL] get_project_documents failed for col='%s': %s",
                collection,
                exc,
            )
            raw = []

        records = [
            DocumentRecord(
                id=item["id"],
                document=item["document"],
                metadata=item.get("metadata", {}),
                collection=collection,
            )
            for item in raw
        ]

        return ProjectDocumentsResponse(
            project_id=project_id,
            collection=collection,
            documents=records,
            total=len(records),
        )

    async def get_provider_health(self) -> HealthResponse:
        """
        Probe the active embedding provider and return health status.

        Returns:
            HealthResponse with provider name, dimension, and health status.
        """
        from memory.manager import default_manager

        try:
            result = default_manager.health_check()
            provider = default_manager.get_embedding_provider()

            # Determine human-readable mode
            name = result.provider_name
            if name == "ollama":
                mode = "local"
            elif name == "huggingface":
                mode = "cloud"
            else:
                mode = "fallback"

            status = "healthy" if result.healthy else "degraded"
            return HealthResponse(
                status=status,
                embedding_provider=name,
                embedding_dimension=provider.dimension,
                provider_healthy=result.healthy,
                mode=mode,
                detail=result.error if hasattr(result, "error") else None,
            )
        except Exception as exc:
            logger.error("[RAG-RETRIEVAL] Health check failed: %s", exc)
            return HealthResponse(
                status="degraded",
                embedding_provider="unknown",
                embedding_dimension=0,
                provider_healthy=False,
                mode="fallback",
                detail=str(exc),
            )

    async def get_collections(self) -> CollectionsResponse:
        """Return the list of all registered RAG collection names."""
        cols = rag_settings.get_collections()
        return CollectionsResponse(collections=cols, total=len(cols))
