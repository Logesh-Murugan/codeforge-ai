"""
IndexingService — Phase 5.2

Vector index management: inspect, clear, and report on ChromaDB collections.

Operations:
    get_index_status()           — Per-collection document counts for a project
    delete_project_index()       — Wipe all collections for a project
    delete_collection_index()    — Wipe a single collection for a project
"""
from __future__ import annotations

import logging
from typing import Optional

from rag.config import rag_settings
from rag.schemas.indexing import DeleteIndexResponse, IndexStatus

logger = logging.getLogger(__name__)


class IndexingService:
    """
    Index management service for the RAG pipeline.

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

    def _get_chroma_store(self):
        """Return the underlying ChromaVectorStore."""
        svc = self._get_service()
        return svc._store

    # ── Public API ───────────────────────────────────────────────────────

    async def get_index_status(self, project_id: int) -> IndexStatus:
        """
        Return document counts per collection for a project.

        Queries ChromaDB for the number of documents belonging to ``project_id``
        in each registered collection.

        Args:
            project_id: Owning project identifier.

        Returns:
            IndexStatus with per-collection counts and total.
        """
        store = self._get_chroma_store()
        collections = rag_settings.get_collections()
        counts: dict = {}

        for col in collections:
            try:
                # Get all docs for the project in this collection
                raw = store.get_all(col, project_id)
                doc_count = len(raw.get("ids", []))
                counts[col] = doc_count
            except Exception as exc:
                logger.warning(
                    "[RAG-INDEXING] Could not count documents in '%s': %s", col, exc
                )
                counts[col] = 0

        total = sum(counts.values())
        logger.info(
            "[RAG-INDEXING] Index status for project=%d: total=%d across %d collections",
            project_id,
            total,
            len(collections),
        )

        return IndexStatus(
            project_id=project_id,
            collections=counts,
            total_documents=total,
        )

    async def delete_project_index(self, project_id: int) -> DeleteIndexResponse:
        """
        Wipe all vector embeddings for a project across all collections.

        This is a hard delete from ChromaDB — the data is not recoverable.
        PostgreSQL persistent memory (Phase 5.1) is NOT affected.

        Args:
            project_id: Owning project identifier.

        Returns:
            DeleteIndexResponse confirming the deletion.
        """
        svc = self._get_service()

        logger.info(
            "[RAG-INDEXING] Deleting all vector embeddings for project=%d", project_id
        )

        try:
            svc.delete_project_memory(project_id)
            logger.info(
                "[RAG-INDEXING] Successfully deleted all embeddings for project=%d",
                project_id,
            )
        except Exception as exc:
            logger.error(
                "[RAG-INDEXING] Failed to delete project index for project=%d: %s",
                project_id,
                exc,
            )
            raise RuntimeError(
                f"Failed to delete index for project {project_id}: {exc}"
            ) from exc

        return DeleteIndexResponse(
            message=f"All vector embeddings deleted for project {project_id}.",
            project_id=project_id,
            collection=None,
        )

    async def delete_collection_index(
        self,
        project_id: int,
        collection: str,
    ) -> DeleteIndexResponse:
        """
        Wipe all vector embeddings for a project within a single collection.

        Args:
            project_id: Owning project identifier.
            collection: Target collection name.

        Returns:
            DeleteIndexResponse confirming the deletion.
        """
        known_collections = set(rag_settings.get_collections())
        if collection not in known_collections:
            raise ValueError(
                f"Unknown collection '{collection}'. "
                f"Valid collections: {', '.join(sorted(known_collections))}"
            )

        store = self._get_chroma_store()

        logger.info(
            "[RAG-INDEXING] Deleting embeddings for project=%d collection='%s'",
            project_id,
            collection,
        )

        try:
            store.delete_by_project(collection, project_id)
            logger.info(
                "[RAG-INDEXING] Deleted embeddings in '%s' for project=%d",
                collection,
                project_id,
            )
        except Exception as exc:
            logger.error(
                "[RAG-INDEXING] Failed to delete collection index '%s' for project=%d: %s",
                collection,
                project_id,
                exc,
            )
            raise RuntimeError(
                f"Failed to delete index for collection '{collection}': {exc}"
            ) from exc

        return DeleteIndexResponse(
            message=f"Vector embeddings deleted for project {project_id} in '{collection}'.",
            project_id=project_id,
            collection=collection,
        )
