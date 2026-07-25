"""
StorageEngine — Phase 3.3 RAG Pipeline.

Responsibilities
----------------
- Accept a list of ChunkRecords and write them to the vector store in
  configurable batches.
- Optionally deduplicate on content hash before writing.
- Optionally mirror every ingestion into the ``project_history``
  collection for version tracking (Phase 3.4).
- Return a structured IngestionResult summary.
"""
from __future__ import annotations

import datetime
import logging
from typing import Any, Dict, List, Optional, Set

from memory.interfaces import EmbeddingProviderInterface, VectorStoreInterface
from memory.rag.schemas import ChunkRecord, IngestionResult, StorageConfig

logger = logging.getLogger(__name__)

_HISTORY_COLLECTION = "project_history"


class StorageEngine:
    """
    Batch ingestion layer for the RAG pipeline.

    Args:
        embedding_provider: Provider used to embed chunk content.
        vector_store:       Backend where vectors are persisted.
        config:             Storage behaviour configuration.
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProviderInterface,
        vector_store: VectorStoreInterface,
        config: Optional[StorageConfig] = None,
    ) -> None:
        self._embed = embedding_provider
        self._store = vector_store
        self.config = config or StorageConfig()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ingest(
        self,
        chunks: List[ChunkRecord],
        project_id: int,
        agent_name: str,
        artifact_type: str,
        collection_name: str,
        version: int = 1,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> IngestionResult:
        """
        Embed and persist a list of chunks.

        Args:
            chunks:          Chunks produced by :class:`ChunkingEngine`.
            project_id:      Owning project.
            agent_name:      Agent that produced these chunks.
            artifact_type:   Descriptor (e.g. ``"python_code"``).
            collection_name: Target ChromaDB collection.
            version:         Artifact version number.
            extra_metadata:  Additional key/value pairs merged into each
                             chunk's stored metadata.

        Returns:
            An :class:`IngestionResult` summary.
        """
        if not chunks:
            return IngestionResult(
                project_id=project_id,
                collection_name=collection_name,
                total_chunks=0,
                stored_chunks=0,
                skipped_chunks=0,
                first_id="",
                version=version,
            )

        timestamp = datetime.datetime.utcnow().isoformat()

        # --- Deduplication pass -------------------------------------------
        existing_hashes: Set[str] = set()
        if self.config.deduplicate:
            existing_hashes = self._fetch_existing_hashes(collection_name, project_id)

        to_store: List[ChunkRecord] = []
        skipped = 0
        for chunk in chunks:
            if self.config.deduplicate and chunk.content_hash in existing_hashes:
                logger.debug(
                    "[STORAGE] Skipping duplicate chunk (hash=%s) in '%s'",
                    chunk.content_hash[:12],
                    collection_name,
                )
                skipped += 1
            else:
                to_store.append(chunk)
                existing_hashes.add(chunk.content_hash)  # prevent in-batch dupes

        if not to_store:
            return IngestionResult(
                project_id=project_id,
                collection_name=collection_name,
                total_chunks=len(chunks),
                stored_chunks=0,
                skipped_chunks=skipped,
                first_id="",
                version=version,
            )

        # --- Build flat metadata list -------------------------------------
        metadatas: List[Dict[str, Any]] = []
        ids: List[str] = []
        documents: List[str] = []

        for chunk in to_store:
            meta: Dict[str, Any] = {
                "project_id": project_id,
                "agent_name": agent_name,
                "artifact_type": artifact_type,
                "timestamp": timestamp,
                "version": version,
                "chunk_index": chunk.chunk_index,
                "total_chunks": chunk.total_chunks,
                "content_hash": chunk.content_hash,
                "strategy": chunk.strategy.value,
            }
            if extra_metadata:
                meta.update(extra_metadata)
            ids.append(chunk.chunk_id)
            documents.append(chunk.content)
            metadatas.append(meta)

        # --- Batch embedding + write --------------------------------------
        first_id = ids[0]
        batch_size = self.config.batch_size

        for batch_start in range(0, len(to_store), batch_size):
            batch_ids = ids[batch_start: batch_start + batch_size]
            batch_docs = documents[batch_start: batch_start + batch_size]
            batch_meta = metadatas[batch_start: batch_start + batch_size]

            embeddings = self._embed.embed_documents(batch_docs)
            self._store.store(
                collection_name=collection_name,
                ids=batch_ids,
                documents=batch_docs,
                embeddings=embeddings,
                metadatas=batch_meta,
            )
            logger.info(
                "[STORAGE] Wrote batch %d-%d (%d chunks) to '%s'",
                batch_start,
                batch_start + len(batch_ids) - 1,
                len(batch_ids),
                collection_name,
            )

        # --- Optional version mirror --------------------------------------
        if self.config.versioning_enabled and collection_name != _HISTORY_COLLECTION:
            self._mirror_to_history(
                to_store, ids, documents, metadatas, project_id, version
            )

        return IngestionResult(
            project_id=project_id,
            collection_name=collection_name,
            total_chunks=len(chunks),
            stored_chunks=len(to_store),
            skipped_chunks=skipped,
            first_id=first_id,
            version=version,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fetch_existing_hashes(self, collection_name: str, project_id: int) -> Set[str]:
        """Pull content_hash values for all existing docs in this project/collection."""
        try:
            raw = self._store.get_all(collection_name, project_id)
            metadatas = raw.get("metadatas") or []
            return {
                m["content_hash"]
                for m in metadatas
                if isinstance(m, dict) and "content_hash" in m
            }
        except Exception as exc:
            logger.debug("[STORAGE] Could not fetch existing hashes: %s", exc)
            return set()

    def _mirror_to_history(
        self,
        chunks: List[ChunkRecord],
        ids: List[str],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        project_id: int,
        version: int,
    ) -> None:
        """Write a snapshot copy into ``project_history``."""
        try:
            history_meta = [
                {**m, "source_collection": metadatas[i].get("artifact_type", "")}
                for i, m in enumerate(metadatas)
            ]
            history_ids = [f"hist-{doc_id}" for doc_id in ids]
            embeddings = self._embed.embed_documents(documents)
            self._store.store(
                collection_name=_HISTORY_COLLECTION,
                ids=history_ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=history_meta,
            )
            logger.debug(
                "[STORAGE] Mirrored %d chunks to '%s' (v%d)",
                len(ids),
                _HISTORY_COLLECTION,
                version,
            )
        except Exception as exc:
            logger.warning("[STORAGE] History mirror failed (non-fatal): %s", exc)
