"""
RetrievalEngine — Phase 3.3 RAG Pipeline.

Provides:
- Single-collection semantic search
- Multi-collection fan-out with global re-ranking
- Metadata filtering (passed to ChromaDB ``where`` clause)
- Maximal Marginal Relevance (MMR) deduplication
- Configurable limit and similarity threshold
"""
from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional

from memory.interfaces import EmbeddingProviderInterface, VectorStoreInterface
from memory.rag.schemas import (
    FilterOperator,
    MetadataFilter,
    RetrievalConfig,
    RetrievalResult,
)
from memory.utils.similarity import cosine_similarity

logger = logging.getLogger(__name__)

# Collections that hold operational metadata — excluded from default fan-out
_META_COLLECTIONS = {"conversation", "project_history"}


class RetrievalEngine:
    """
    Semantic retrieval engine.

    Args:
        embedding_provider: Provider used to embed search queries.
        vector_store:       Backend to query.
        config:             Retrieval behaviour configuration.
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProviderInterface,
        vector_store: VectorStoreInterface,
        config: Optional[RetrievalConfig] = None,
    ) -> None:
        self._embed = embedding_provider
        self._store = vector_store
        self.config = config or RetrievalConfig()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        project_id: int,
        collection_name: str,
        metadata_filter: Optional[MetadataFilter] = None,
        limit: Optional[int] = None,
        threshold: Optional[float] = None,
    ) -> List[RetrievalResult]:
        """
        Semantic search within a single collection.

        Args:
            query:           Natural-language search query.
            project_id:      Project scope filter.
            collection_name: Collection to search.
            metadata_filter: Optional extra metadata conditions.
            limit:           Override config limit.
            threshold:       Override config threshold.

        Returns:
            List of :class:`RetrievalResult` sorted by descending similarity.
        """
        if not query.strip():
            return []

        effective_limit = limit if limit is not None else self.config.limit
        effective_threshold = threshold if threshold is not None else self.config.threshold

        query_vector = self._embed_query_safe(query)
        if query_vector is None:
            return []

        where = self._build_where(project_id, metadata_filter)

        try:
            raw = self._store.query(
                collection_name=collection_name,
                query_embeddings=[query_vector],
                project_id=project_id,
                limit=effective_limit,
                where=where,
            )
        except Exception as exc:
            logger.error("[RETRIEVAL] Query failed on '%s': %s", collection_name, exc)
            return []

        ranked = self._rerank(raw, query_vector, collection_name, effective_threshold)

        if self.config.use_mmr:
            ranked = self._mmr(ranked, query_vector, effective_limit)
        else:
            ranked = ranked[:effective_limit]

        return ranked

    def search_multi(
        self,
        query: str,
        project_id: int,
        collections: Optional[List[str]] = None,
        metadata_filter: Optional[MetadataFilter] = None,
        limit: Optional[int] = None,
        threshold: Optional[float] = None,
    ) -> List[RetrievalResult]:
        """
        Fan-out semantic search across multiple collections.

        Results from all collections are merged and globally re-ranked
        by similarity score.  MMR (if enabled) is applied after merging.

        Args:
            query:           Search query.
            project_id:      Project scope.
            collections:     Collections to fan out to.  ``None`` = all
                             domain collections (excludes conversation /
                             project_history).
            metadata_filter: Optional metadata conditions.
            limit:           Total results cap after merging.
            threshold:       Minimum similarity across all collections.

        Returns:
            Globally ranked list of :class:`RetrievalResult`.
        """
        if not query.strip():
            return []

        effective_limit = limit if limit is not None else self.config.limit
        effective_threshold = threshold if threshold is not None else self.config.threshold

        if collections is None:
            from memory.vectorstores.chroma import ChromaVectorStore
            collections = [
                c for c in ChromaVectorStore.COLLECTION_TYPES
                if c not in _META_COLLECTIONS
            ]

        query_vector = self._embed_query_safe(query)
        if query_vector is None:
            return []

        where = self._build_where(project_id, metadata_filter)
        all_results: List[RetrievalResult] = []

        for col in collections:
            try:
                raw = self._store.query(
                    collection_name=col,
                    query_embeddings=[query_vector],
                    project_id=project_id,
                    limit=effective_limit,
                    where=where,
                )
                ranked = self._rerank(raw, query_vector, col, effective_threshold)
                all_results.extend(ranked)
            except Exception as exc:
                logger.debug("[RETRIEVAL] Skipping collection '%s': %s", col, exc)

        # Global sort by similarity
        all_results.sort(key=lambda r: r.similarity_score, reverse=True)

        if self.config.use_mmr:
            all_results = self._mmr(all_results, query_vector, effective_limit)
        else:
            all_results = all_results[:effective_limit]

        return all_results

    # ------------------------------------------------------------------
    # Re-ranking using exact cosine similarity
    # ------------------------------------------------------------------

    def _rerank(
        self,
        raw: Dict[str, Any],
        query_vector: List[float],
        collection_name: str,
        threshold: float,
    ) -> List[RetrievalResult]:
        """Fetch stored embeddings and re-score with exact cosine similarity."""
        ids = raw.get("ids", [[]])[0]
        if not ids:
            return []

        try:
            col = self._store.get_collection(collection_name)
            detail = col.get(ids=ids, include=["embeddings", "documents", "metadatas"])
            candidate_embeddings: List[List[float]] = detail.get("embeddings") or []
            documents: List[str] = detail.get("documents") or []
            metadatas: List[dict] = detail.get("metadatas") or []
        except Exception as exc:
            logger.warning("[RETRIEVAL] Re-rank fetch failed for '%s': %s", collection_name, exc)
            # Fall back to using ANN distances from raw results
            candidate_embeddings = []
            documents = raw.get("documents", [[]])[0]
            metadatas = raw.get("metadatas", [[]])[0]

        results: List[RetrievalResult] = []
        for idx, doc_id in enumerate(ids):
            if idx >= len(documents):
                break
            doc = documents[idx]
            meta = metadatas[idx] if idx < len(metadatas) else {}

            if candidate_embeddings and idx < len(candidate_embeddings):
                score = cosine_similarity(query_vector, candidate_embeddings[idx])
            else:
                # No stored embeddings — use 1 - distance from raw ANN results
                distances = raw.get("distances", [[]])[0]
                score = 1.0 - distances[idx] if idx < len(distances) else 0.0

            if score >= threshold:
                results.append(
                    RetrievalResult(
                        id=doc_id,
                        document=doc,
                        metadata=meta,
                        similarity_score=score,
                        collection=collection_name,
                    )
                )

        results.sort(key=lambda r: r.similarity_score, reverse=True)
        return results

    # ------------------------------------------------------------------
    # Maximal Marginal Relevance
    # ------------------------------------------------------------------

    def _mmr(
        self,
        candidates: List[RetrievalResult],
        query_vector: List[float],
        k: int,
    ) -> List[RetrievalResult]:
        """
        Apply Maximal Marginal Relevance to select *k* diverse results.

        MMR score = λ · similarity(query, doc) − (1−λ) · max_similarity(doc, selected)

        λ is taken from ``self.config.mmr_lambda``.
        """
        if not candidates or k <= 0:
            return candidates[:k]

        lam = self.config.mmr_lambda
        selected: List[RetrievalResult] = []
        remaining = list(candidates)

        # Pre-fetch stored embeddings for MMR distance computation
        # We use the similarity_score as a proxy since we don't hold vectors here.
        # For full MMR we re-embed on the fly — use scores as magnitude approximation.

        while remaining and len(selected) < k:
            best_idx = 0
            best_score = -float("inf")

            for i, cand in enumerate(remaining):
                rel = cand.similarity_score  # relevance to query

                if not selected:
                    mmr_score = rel
                else:
                    # Diversity: similarity to already-selected docs via score proxy
                    max_sim_to_selected = max(
                        self._doc_similarity_proxy(cand, sel) for sel in selected
                    )
                    mmr_score = lam * rel - (1.0 - lam) * max_sim_to_selected

                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = i

            selected.append(remaining.pop(best_idx))

        return selected

    @staticmethod
    def _doc_similarity_proxy(a: RetrievalResult, b: RetrievalResult) -> float:
        """
        Proxy inter-document similarity using metadata overlap and score proximity.

        When two chunks come from the same collection and have similar scores
        they are likely near-duplicates — a rough but dependency-free heuristic.
        """
        same_collection = 1.0 if a.collection == b.collection else 0.3
        score_proximity = 1.0 - abs(a.similarity_score - b.similarity_score)
        return same_collection * score_proximity * 0.5

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _embed_query_safe(self, query: str) -> Optional[List[float]]:
        """Embed a query, returning None on failure."""
        try:
            return self._embed.embed_query(query)
        except Exception as exc:
            logger.error("[RETRIEVAL] Query embedding failed: %s", exc)
            return None

    def _build_where(
        self,
        project_id: int,
        metadata_filter: Optional[MetadataFilter],
    ) -> Optional[Dict[str, Any]]:
        """
        Build the ChromaDB ``where`` clause, merging project_id with any
        caller-supplied metadata conditions.
        """
        project_clause = {"project_id": {"$eq": project_id}}

        if not metadata_filter or not metadata_filter.conditions:
            return project_clause

        extra = metadata_filter.to_chroma_where()
        if extra is None:
            return project_clause

        return {"$and": [project_clause, extra]}
