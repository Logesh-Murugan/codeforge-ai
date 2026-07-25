"""
RAGPipeline — Phase 3.3.

The top-level assembled pipeline.  Composes ChunkingEngine, StorageEngine,
and RetrievalEngine into a single, easy-to-use class.

Usage
-----
    from memory.rag import RAGPipeline, RAGConfig

    pipeline = RAGPipeline.from_service(memory_service)

    # Ingest an agent output
    result = pipeline.ingest(
        text=backend_code,
        project_id=42,
        agent_name="backend_developer",
        artifact_type="python_code",
        collection_name="backend_code",
        version=1,
    )

    # Retrieve context
    results = pipeline.retrieve(
        query="FastAPI authentication middleware",
        project_id=42,
    )
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from memory.interfaces import EmbeddingProviderInterface, VectorStoreInterface
from memory.rag.chunker import ChunkingEngine
from memory.rag.retrieval import RetrievalEngine
from memory.rag.schemas import (
    ChunkingConfig,
    IngestionResult,
    MetadataFilter,
    RAGConfig,
    RetrievalConfig,
    RetrievalResult,
    StorageConfig,
)
from memory.rag.storage import StorageEngine

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Full Retrieval-Augmented Generation pipeline.

    Wires together:
        ChunkingEngine  → splits raw text into chunks
        StorageEngine   → embeds + persists chunks to ChromaDB
        RetrievalEngine → semantic search + re-ranking + MMR

    Args:
        embedding_provider: Embedding backend.
        vector_store:       Vector store backend.
        config:             Optional :class:`RAGConfig` overriding defaults.
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProviderInterface,
        vector_store: VectorStoreInterface,
        config: Optional[RAGConfig] = None,
    ) -> None:
        cfg = config or RAGConfig()

        self._chunker = ChunkingEngine(cfg.chunking)
        self._storage = StorageEngine(embedding_provider, vector_store, cfg.storage)
        self._retrieval = RetrievalEngine(embedding_provider, vector_store, cfg.retrieval)
        self.config = cfg

        logger.info(
            "[RAG] Pipeline ready — strategy=%s chunk_size=%d overlap=%d",
            cfg.chunking.strategy.value,
            cfg.chunking.chunk_size,
            cfg.chunking.overlap,
        )

    # ------------------------------------------------------------------
    # Convenience factory
    # ------------------------------------------------------------------

    @classmethod
    def from_service(cls, service: Any, config: Optional[RAGConfig] = None) -> "RAGPipeline":
        """
        Build a RAGPipeline from an existing :class:`MemoryService` instance.

        This avoids re-constructing providers when the service is already
        wired in the application.

        Args:
            service: A ``MemoryService`` instance (uses ``_embed`` and ``_store``).
            config:  Optional config override.
        """
        return cls(
            embedding_provider=service._embed,
            vector_store=service._store,
            config=config,
        )

    # ------------------------------------------------------------------
    # Ingest
    # ------------------------------------------------------------------

    def ingest(
        self,
        text: str,
        project_id: int,
        agent_name: str,
        artifact_type: str,
        collection_name: str,
        version: int = 1,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> IngestionResult:
        """
        Chunk, embed and persist one text document.

        This is the primary write path for agent outputs.

        Args:
            text:            Raw text to ingest (may be arbitrarily long).
            project_id:      Owning project.
            agent_name:      Agent that produced the text.
            artifact_type:   Descriptor (e.g. ``"python_code"``).
            collection_name: Target ChromaDB collection.
            version:         Artifact version number.
            extra_metadata:  Extra key/value pairs stored in each chunk.

        Returns:
            :class:`IngestionResult` summary.
        """
        if not text or not text.strip():
            return IngestionResult(
                project_id=project_id,
                collection_name=collection_name,
                total_chunks=0,
                stored_chunks=0,
                skipped_chunks=0,
                first_id="",
                version=version,
            )

        meta = extra_metadata or {}
        meta.update({"agent_name": agent_name, "artifact_type": artifact_type})

        chunks = self._chunker.chunk(
            text,
            artifact_type=artifact_type,
            extra_metadata=meta,
        )

        return self._storage.ingest(
            chunks=chunks,
            project_id=project_id,
            agent_name=agent_name,
            artifact_type=artifact_type,
            collection_name=collection_name,
            version=version,
            extra_metadata=extra_metadata,
        )

    # ------------------------------------------------------------------
    # Retrieve
    # ------------------------------------------------------------------

    def retrieve(
        self,
        query: str,
        project_id: int,
        collection_name: Optional[str] = None,
        metadata_filter: Optional[MetadataFilter] = None,
        limit: Optional[int] = None,
        threshold: Optional[float] = None,
    ) -> List[RetrievalResult]:
        """
        Semantic search.

        When *collection_name* is given, searches that single collection.
        When omitted, fans out across all domain collections.

        Args:
            query:           Natural-language search query.
            project_id:      Project scope.
            collection_name: Single collection, or ``None`` for fan-out.
            metadata_filter: Optional additional metadata conditions.
            limit:           Override config limit.
            threshold:       Override config similarity threshold.

        Returns:
            List of :class:`RetrievalResult` sorted by descending similarity.
        """
        if collection_name:
            return self._retrieval.search(
                query=query,
                project_id=project_id,
                collection_name=collection_name,
                metadata_filter=metadata_filter,
                limit=limit,
                threshold=threshold,
            )

        return self._retrieval.search_multi(
            query=query,
            project_id=project_id,
            metadata_filter=metadata_filter,
            limit=limit,
            threshold=threshold,
        )

    # ------------------------------------------------------------------
    # Config hot-reload
    # ------------------------------------------------------------------

    def reconfigure(self, config: RAGConfig) -> None:
        """
        Replace the pipeline configuration at runtime.

        Re-creates ChunkingEngine with the new config; the storage and
        retrieval engines update their configs in-place.
        """
        self._chunker = ChunkingEngine(config.chunking)
        self._storage.config = config.storage
        self._retrieval.config = config.retrieval
        self.config = config
        logger.info("[RAG] Pipeline reconfigured: %s", config.model_dump())
