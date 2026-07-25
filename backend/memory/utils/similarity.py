"""
Cosine-similarity utilities for the RAG retrieval pipeline.

No external dependencies — pure Python arithmetic.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """
    Return the cosine similarity between two equal-length float vectors.

    Returns 0.0 when either vector is a zero-vector or the lengths differ,
    rather than raising an exception.
    """
    if len(vec_a) != len(vec_b) or not vec_a:
        return 0.0

    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot / (norm_a * norm_b)


def rank_results(
    raw_query_results: Dict[str, Any],
    query_vector: List[float],
    candidate_embeddings: List[List[float]],
    threshold: float = 0.0,
) -> List[Dict[str, Any]]:
    """
    Re-rank raw vector-store results using exact cosine similarity and
    filter out entries below *threshold*.

    Args:
        raw_query_results:    Raw dict from the vector store backend
                              (must contain ``ids``, ``documents``,
                              ``metadatas`` as nested lists).
        query_vector:         Embedding of the search query.
        candidate_embeddings: Embeddings of the candidate documents,
                              in the same order as the result lists.
        threshold:            Minimum similarity score (inclusive).

    Returns:
        List of dicts sorted by descending similarity_score::

            [{"id": str, "document": str,
              "metadata": dict, "similarity_score": float}, ...]
    """
    documents = raw_query_results.get("documents", [[]])[0]
    metadatas = raw_query_results.get("metadatas", [[]])[0]
    ids = raw_query_results.get("ids", [[]])[0]

    ranked: List[Dict[str, Any]] = []
    for idx, doc in enumerate(documents):
        if idx >= len(candidate_embeddings):
            break
        score = cosine_similarity(query_vector, candidate_embeddings[idx])
        if score >= threshold:
            ranked.append(
                {
                    "id": ids[idx],
                    "document": doc,
                    "metadata": metadatas[idx],
                    "similarity_score": score,
                }
            )

    ranked.sort(key=lambda x: x["similarity_score"], reverse=True)
    return ranked
