"""
Backward-compatibility shim.

Old import path:  from memory.retrieval import CosineSimilarityScorer
                  from memory.retrieval import rank_and_filter_results

New import path:  from memory.utils import cosine_similarity, rank_results
"""
from memory.utils.similarity import cosine_similarity, rank_results

# Legacy class wrapper so old `CosineSimilarityScorer.calculate(a, b)` calls work
class CosineSimilarityScorer:
    """Thin shim preserving the old static-method API."""

    @staticmethod
    def calculate(vec1, vec2) -> float:
        return cosine_similarity(vec1, vec2)


# Legacy function alias
def rank_and_filter_results(
    raw_query_results,
    query_vector,
    embeddings,
    threshold=0.0,
):
    return rank_results(
        raw_query_results=raw_query_results,
        query_vector=query_vector,
        candidate_embeddings=embeddings,
        threshold=threshold,
    )


__all__ = [
    "CosineSimilarityScorer",
    "rank_and_filter_results",
    "cosine_similarity",
    "rank_results",
]
