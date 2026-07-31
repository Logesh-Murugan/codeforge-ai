"""
Memory subsystem utilities package.

Public API
----------
from memory.utils import cosine_similarity, rank_results
from memory.utils import chunk_text, chunk_documents
from memory.utils import CachedEmbeddingProvider
from memory.utils import inject_domain_fields, extract_domain_fields
"""
from memory.utils.similarity import cosine_similarity, rank_results
from memory.utils.chunking import chunk_text, chunk_documents
from memory.utils.cache import CachedEmbeddingProvider
from memory.utils.memory_helpers import (
    inject_domain_fields,
    extract_domain_fields,
    merge_metadata,
    sanitize_content,
    validate_domain,
    build_search_metadata,
    format_memory_response,
    VALID_DOMAINS,
)

__all__ = [
    "cosine_similarity",
    "rank_results",
    "chunk_text",
    "chunk_documents",
    "CachedEmbeddingProvider",
    # Phase 5.1 helpers
    "inject_domain_fields",
    "extract_domain_fields",
    "merge_metadata",
    "sanitize_content",
    "validate_domain",
    "build_search_metadata",
    "format_memory_response",
    "VALID_DOMAINS",
]
