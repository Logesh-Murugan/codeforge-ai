"""
MemoryService — unified façade implementing MemoryProviderInterface.

Orchestrates the full memory pipeline:
    store_memory()    → chunk → embed → persist to ChromaDB
    retrieve_memory() → embed query → ANN search → re-rank → filter
    get_project_memory()    → list raw collection entries
    delete_project_memory() → wipe all collections for a project

Context helpers (Phase 3.5):
    build_agent_context()     → assemble injection block for an agent
    store_conversation_turn() → append to conversation memory
    get_conversation_history() → retrieve ordered conversation turns

Project history (Phase 3.4):
    record_version()    → snapshot an artifact with a version number
    get_version_history() → list all snapshots for an artifact

All heavy dependencies (providers, store) are injected via the
constructor — the service itself has no env-var reads.
"""
from __future__ import annotations

import datetime
import logging
import uuid
from typing import Any, Dict, List, Optional

from memory.interfaces import (
    EmbeddingProviderInterface,
    MemoryProviderInterface,
    VectorStoreInterface,
)
from memory.schemas import (
    AgentContext,
    MemoryMetadata,
    MemoryQueryResult,
    ProjectHistoryEntry,
    TextChunk,
)
from memory.utils.chunking import chunk_text
from memory.utils.similarity import rank_results

logger = logging.getLogger(__name__)


class MemoryService(MemoryProviderInterface):
    """
    Unified memory service facade.

    Args:
        embedding_provider: The embedding backend to use.
        vector_store:       The vector storage backend to use.
        chunk_size:         Characters per chunk for long documents.
        chunk_overlap:      Character overlap between consecutive chunks.
    """

    def __init__(
        self,
        embedding_provider: Optional[EmbeddingProviderInterface] = None,
        vector_store: Optional[VectorStoreInterface] = None,
        chunk_size: int = 800,
        chunk_overlap: int = 100,
        # Legacy keyword aliases kept for backward compatibility
        embeddings_provider: Optional[EmbeddingProviderInterface] = None,
        store_manager: Optional[VectorStoreInterface] = None,
    ) -> None:
        # Honour old kwarg names (embeddings_provider, store_manager) as fallbacks
        resolved_embed = embedding_provider or embeddings_provider
        resolved_store = vector_store or store_manager

        if resolved_embed is None:
            from memory.embeddings.local import LocalEmbeddings
            resolved_embed = LocalEmbeddings()
        if resolved_store is None:
            from memory.vectorstores.chroma import ChromaVectorStore
            resolved_store = ChromaVectorStore()

        self._embed = resolved_embed
        self._store = resolved_store
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        logger.info(
            "[SERVICE] MemoryService ready — provider=%s, store=%s, chunk_size=%d",
            self._embed.provider_name,
            type(self._store).__name__,
            self._chunk_size,
        )

    # ======================================================================
    # MemoryProviderInterface — store
    # ======================================================================

    def store_memory(
        self,
        project_id: int,
        agent_name: str,
        artifact_type: str,
        collection_name: str,
        content: str,
        version: int = 1,
    ) -> str:
        """
        Chunk, embed and persist one text artifact.

        If the content is short enough to fit in a single chunk a single
        document is stored.  Long content is automatically split and each
        chunk stored individually; the first chunk's ID is returned.

        Returns:
            The memory ID of the first stored chunk (or "" for empty input).
        """
        if not content.strip():
            logger.warning("[SERVICE] Skipping empty store_memory call.")
            return ""

        timestamp = datetime.datetime.utcnow().isoformat()
        chunks: List[TextChunk] = chunk_text(
            content,
            chunk_size=self._chunk_size,
            overlap=self._chunk_overlap,
            artifact_type=artifact_type,
        )

        first_id = ""
        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for chunk in chunks:
            memory_id = str(uuid.uuid4())
            if not first_id:
                first_id = memory_id
            ids.append(memory_id)
            documents.append(chunk.content)
            metadatas.append(
                {
                    "project_id": project_id,
                    "agent_name": agent_name,
                    "artifact_type": artifact_type,
                    "timestamp": timestamp,
                    "version": version,
                    "chunk_index": chunk.chunk_index,
                    "total_chunks": len(chunks),
                }
            )

        try:
            embeddings = self._embed.embed_documents(documents)
        except Exception as exc:
            logger.error("[SERVICE] Embedding failure: %s", exc)
            raise

        try:
            self._store.store(
                collection_name=collection_name,
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )
            size = self._store.get_collection_size(collection_name)
            logger.info(
                "[SERVICE] Stored %d chunk(s) in '%s' (collection size=%d)",
                len(ids),
                collection_name,
                size,
            )
        except Exception as exc:
            logger.error("[SERVICE] Vector store failure: %s", exc)
            raise

        return first_id

    # ======================================================================
    # MemoryProviderInterface — retrieve
    # ======================================================================

    def retrieve_memory(
        self,
        project_id: int,
        collection_name: str,
        query: str,
        limit: int = 5,
        threshold: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search: embed the query, ANN search, re-rank, filter.

        Returns:
            List of dicts: ``{"id", "document", "metadata", "similarity_score"}``,
            sorted by descending similarity.
        """
        if not query.strip():
            return []

        try:
            query_vector = self._embed.embed_query(query)
        except Exception as exc:
            logger.error("[SERVICE] Query embedding failed: %s", exc)
            return []

        try:
            raw = self._store.query(
                collection_name=collection_name,
                query_embeddings=[query_vector],
                project_id=project_id,
                limit=limit,
            )
        except Exception as exc:
            logger.error("[SERVICE] Vector store query failed: %s", exc)
            return []

        # Fetch the stored embeddings for exact cosine re-ranking
        ids = raw.get("ids", [[]])[0]
        if not ids:
            return []

        try:
            col = self._store.get_collection(collection_name)
            detail = col.get(ids=ids, include=["embeddings", "documents", "metadatas"])
            candidate_embeddings = detail.get("embeddings", [])
        except Exception as exc:
            logger.error("[SERVICE] Embedding fetch for re-ranking failed: %s", exc)
            candidate_embeddings = []

        return rank_results(
            raw_query_results=raw,
            query_vector=query_vector,
            candidate_embeddings=candidate_embeddings,
            threshold=threshold,
        )

    def get_project_memory(
        self, project_id: int, collection_name: str
    ) -> List[Dict[str, Any]]:
        """Return all raw entries for a project in a collection."""
        try:
            raw = self._store.get_all(collection_name, project_id)
        except Exception as exc:
            logger.error("[SERVICE] get_project_memory failed: %s", exc)
            return []

        documents = raw.get("documents", [])
        metadatas = raw.get("metadatas", [])
        ids = raw.get("ids", [])
        return [
            {"id": ids[i], "document": documents[i], "metadata": metadatas[i]}
            for i in range(len(documents))
        ]

    def delete_project_memory(self, project_id: int) -> None:
        """Wipe all project entries across every registered collection."""
        from memory.vectorstores.chroma import ChromaVectorStore

        collection_names = (
            ChromaVectorStore.COLLECTION_TYPES
            if isinstance(self._store, ChromaVectorStore)
            else []
        )
        for col in collection_names:
            try:
                self._store.delete_by_project(col, project_id)
            except Exception as exc:
                logger.error(
                    "[SERVICE] delete_by_project failed on '%s': %s", col, exc
                )

    # ======================================================================
    # Phase 3.5 — Conversation memory
    # ======================================================================

    def store_conversation_turn(
        self,
        project_id: int,
        role: str,
        content: str,
    ) -> str:
        """
        Append one conversation turn to the project's conversation memory.

        Args:
            project_id: Owning project.
            role:       "user" | "assistant" | "system".
            content:    Turn text.

        Returns:
            Memory ID.
        """
        return self.store_memory(
            project_id=project_id,
            agent_name="conversation",
            artifact_type=f"turn:{role}",
            collection_name="conversation",
            content=content,
            version=1,
        )

    def get_conversation_history(
        self,
        project_id: int,
        limit: int = 10,
    ) -> List[Dict[str, str]]:
        """
        Retrieve the most recent conversation turns for a project.

        Returns:
            List of ``{"role": str, "content": str}`` dicts in
            chronological order (oldest first).
        """
        raw = self.get_project_memory(project_id, "conversation")
        # Sort by timestamp ascending
        raw.sort(key=lambda r: r.get("metadata", {}).get("timestamp", ""))
        turns: List[Dict[str, str]] = []
        for entry in raw[-limit:]:
            artifact_type = entry.get("metadata", {}).get("artifact_type", "")
            role = artifact_type.replace("turn:", "") if ":" in artifact_type else "user"
            turns.append({"role": role, "content": entry["document"]})
        return turns

    # ======================================================================
    # Phase 3.5 — Context injection
    # ======================================================================

    def build_agent_context(
        self,
        project_id: int,
        agent_name: str,
        query: str,
        collections: Optional[List[str]] = None,
        limit: int = 5,
        threshold: float = 0.2,
    ) -> AgentContext:
        """
        Assemble a rich context block for an agent.

        Searches *collections* for semantically relevant chunks and
        combines them with recent conversation history.

        Args:
            project_id:   Owning project.
            agent_name:   The agent requesting context.
            query:        Natural-language query to search memory with.
            collections:  Collections to search (defaults to all non-meta
                          collections).
            limit:        Max chunks to include per collection.
            threshold:    Minimum similarity score.

        Returns:
            An :class:`AgentContext` ready for ``.to_prompt_block()``.
        """
        from memory.vectorstores.chroma import ChromaVectorStore

        if collections is None:
            # Default: all domain collections, excluding conversation/history
            all_cols = ChromaVectorStore.COLLECTION_TYPES
            collections = [
                c for c in all_cols
                if c not in ("conversation", "project_history")
            ]

        chunks: List[MemoryQueryResult] = []
        for col in collections:
            try:
                results = self.retrieve_memory(
                    project_id=project_id,
                    collection_name=col,
                    query=query,
                    limit=limit,
                    threshold=threshold,
                )
                for r in results:
                    chunks.append(
                        MemoryQueryResult(
                            id=r["id"],
                            document=r["document"],
                            metadata=r["metadata"],
                            similarity_score=r["similarity_score"],
                        )
                    )
            except Exception as exc:
                logger.debug(
                    "[SERVICE] Context retrieval skipped for '%s': %s", col, exc
                )

        # Sort all chunks globally by similarity
        chunks.sort(key=lambda c: c.similarity_score, reverse=True)
        chunks = chunks[:limit]

        conversation = self.get_conversation_history(project_id, limit=10)

        return AgentContext(
            project_id=project_id,
            agent_name=agent_name,
            chunks=chunks,
            conversation_history=conversation,
        )

    # ======================================================================
    # Phase 3.4 — Project history / version tracking
    # ======================================================================

    def record_version(
        self,
        project_id: int,
        agent_name: str,
        artifact_type: str,
        content: str,
        version: int,
    ) -> str:
        """
        Snapshot an artifact into the ``project_history`` collection.

        Each snapshot is a permanent, immutable record of an artifact
        at a given version number.

        Returns:
            Memory ID.
        """
        return self.store_memory(
            project_id=project_id,
            agent_name=agent_name,
            artifact_type=artifact_type,
            collection_name="project_history",
            content=content,
            version=version,
        )

    def get_version_history(
        self,
        project_id: int,
        artifact_type: Optional[str] = None,
    ) -> List[ProjectHistoryEntry]:
        """
        Return all versioned snapshots for a project, optionally filtered
        by artifact_type.

        Returns:
            List of :class:`ProjectHistoryEntry` sorted by version ascending.
        """
        from memory.schemas import MemoryMetadata, MemoryRecord

        raw = self.get_project_memory(project_id, "project_history")
        entries: List[ProjectHistoryEntry] = []

        for item in raw:
            meta_data = item.get("metadata", {})
            if artifact_type and meta_data.get("artifact_type") != artifact_type:
                continue
            try:
                record = MemoryRecord(
                    id=item["id"],
                    document=item["document"],
                    metadata=MemoryMetadata(**meta_data),
                )
                entries.append(ProjectHistoryEntry.from_memory_record(record))
            except Exception as exc:
                logger.debug("[SERVICE] Skipping malformed history entry: %s", exc)

        entries.sort(key=lambda e: e.version)
        return entries
