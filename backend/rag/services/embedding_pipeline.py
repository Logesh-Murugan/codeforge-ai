"""
EmbeddingPipelineService — Phase 5.2

Async document ingestion pipeline:
    1. Receive raw text document(s)
    2. Chunk with configurable size / overlap
    3. Embed via the active provider (Ollama / HuggingFace / Local)
    4. Upsert into ChromaDB

Delegates all heavy lifting to the existing ``memory.service.MemoryService``
façade (store_memory) to keep a single storage path.
No direct ChromaDB imports — goes through the memory subsystem.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from rag.config import rag_settings
from rag.schemas.indexing import (
    IndexBatchRequest,
    IndexBatchResult,
    IndexRequest,
    IndexResult,
)

logger = logging.getLogger(__name__)


class EmbeddingPipelineService:
    """
    Async document ingestion service for the RAG pipeline.

    Args:
        memory_service: Optional injected MemoryService for testing.
                        When None, resolved from ``memory.manager.default_manager``.
    """

    def __init__(self, memory_service=None) -> None:
        self._memory_service = memory_service

    # ── Private helpers ─────────────────────────────────────────────────

    def _get_service(self):
        """Return the active MemoryService (lazy-resolved)."""
        if self._memory_service is not None:
            return self._memory_service
        from memory.manager import default_manager
        return default_manager.get_service()

    @staticmethod
    def _count_chunks(content: str, chunk_size: int, overlap: int) -> int:
        """Estimate number of chunks without calling the chunker."""
        if not content:
            return 0
        if len(content) <= chunk_size:
            return 1
        step = max(1, chunk_size - overlap)
        return max(1, -(-len(content) // step))  # ceiling division approximation

    # ── Public API ───────────────────────────────────────────────────────

    async def ingest(self, request: IndexRequest) -> IndexResult:
        """
        Chunk, embed, and store a single document.

        Runs the store_memory pipeline synchronously within the async context
        (MemoryService.store_memory is a sync method backed by ChromaDB which
        uses its own thread-safe client).

        Args:
            request: Validated IndexRequest.

        Returns:
            IndexResult with the first chunk's memory ID and total chunks stored.

        Raises:
            ValueError: If the content is empty after stripping.
            RuntimeError: If embedding or storage fails.
        """
        content = request.content.strip()
        if not content:
            raise ValueError("Content must not be empty after stripping whitespace.")

        svc = self._get_service()

        logger.info(
            "[RAG-PIPELINE] Ingesting document for project=%d collection=%s "
            "artifact_type=%s len=%d",
            request.project_id,
            request.collection,
            request.artifact_type,
            len(content),
        )

        memory_id = svc.store_memory(
            project_id=request.project_id,
            agent_name=request.agent_name,
            artifact_type=request.artifact_type,
            collection_name=request.collection,
            content=content,
            version=request.version,
        )

        # Estimate chunk count from known chunk size / overlap
        chunks_stored = self._count_chunks(
            content,
            chunk_size=rag_settings.RAG_CHUNK_SIZE,
            overlap=rag_settings.RAG_CHUNK_OVERLAP,
        )

        logger.info(
            "[RAG-PIPELINE] Stored ~%d chunk(s), memory_id=%s",
            chunks_stored,
            memory_id,
        )

        return IndexResult(
            memory_id=memory_id,
            chunks_stored=chunks_stored,
            collection=request.collection,
            project_id=request.project_id,
            artifact_type=request.artifact_type,
            indexed_at=datetime.now(timezone.utc),
        )

    async def ingest_batch(self, request: IndexBatchRequest) -> IndexBatchResult:
        """
        Chunk, embed, and store multiple documents in one call.

        Each document is processed independently. Failures are logged and
        counted but do NOT abort the remaining documents.

        Args:
            request: Validated IndexBatchRequest (max 50 documents).

        Returns:
            IndexBatchResult with per-document results and failure count.
        """
        max_docs = rag_settings.RAG_BATCH_MAX_DOCUMENTS
        docs = request.documents[:max_docs]

        results: List[IndexResult] = []
        total_chunks = 0
        failed = 0

        for doc in docs:
            sub_request = IndexRequest(
                project_id=request.project_id,
                collection=request.collection,
                content=doc.content,
                artifact_type=doc.artifact_type,
                agent_name=doc.agent_name,
                version=doc.version,
                metadata=doc.metadata,
            )
            try:
                result = await self.ingest(sub_request)
                results.append(result)
                total_chunks += result.chunks_stored
            except Exception as exc:
                failed += 1
                logger.error(
                    "[RAG-PIPELINE] Batch ingest failed for doc (artifact_type=%s): %s",
                    doc.artifact_type,
                    exc,
                )

        logger.info(
            "[RAG-PIPELINE] Batch complete: project=%d collection=%s "
            "docs=%d chunks=%d failed=%d",
            request.project_id,
            request.collection,
            len(docs),
            total_chunks,
            failed,
        )

        return IndexBatchResult(
            project_id=request.project_id,
            collection=request.collection,
            total_documents=len(docs),
            total_chunks=total_chunks,
            results=results,
            failed=failed,
            indexed_at=datetime.now(timezone.utc),
        )
