"""
Memory subsystem utilities package.

Public API
----------
from memory.utils import cosine_similarity, rank_results
from memory.utils import chunk_text, chunk_documents
from memory.utils import CachedEmbeddingProvider
"""
from memory.utils.similarity import cosine_similarity, rank_results
from memory.utils.chunking import chunk_text, chunk_documents
from memory.utils.cache import CachedEmbeddingProvider

__all__ = [
    "cosine_similarity",
    "rank_results",
    "chunk_text",
    "chunk_documents",
    "CachedEmbeddingProvider",
]
