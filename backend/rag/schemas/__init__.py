"""
RAG Engine schemas — Phase 5.2

Re-exports all public schema classes for convenience::

    from rag.schemas import IndexRequest, SearchRequest, ContextRequest
"""
from rag.schemas.indexing import (
    IndexDocument,
    IndexRequest,
    IndexBatchRequest,
    IndexResult,
    IndexBatchResult,
    IndexStatus,
    DeleteIndexResponse,
)
from rag.schemas.retrieval import (
    SearchRequest,
    SearchResult,
    SearchResponse,
    SimilarityRequest,
    SimilarityResult,
    SimilarityResponse,
    DocumentRecord,
    ProjectDocumentsResponse,
    CollectionsResponse,
    HealthResponse,
)
from rag.schemas.context import (
    ContextRequest,
    ContextChunk,
    ContextBlock,
    ContextResponse,
)

__all__ = [
    # Indexing
    "IndexDocument",
    "IndexRequest",
    "IndexBatchRequest",
    "IndexResult",
    "IndexBatchResult",
    "IndexStatus",
    "DeleteIndexResponse",
    # Retrieval
    "SearchRequest",
    "SearchResult",
    "SearchResponse",
    "SimilarityRequest",
    "SimilarityResult",
    "SimilarityResponse",
    "DocumentRecord",
    "ProjectDocumentsResponse",
    "CollectionsResponse",
    "HealthResponse",
    # Context
    "ContextRequest",
    "ContextChunk",
    "ContextBlock",
    "ContextResponse",
]
