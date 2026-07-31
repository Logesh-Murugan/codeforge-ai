"""
RAG services package — Phase 5.2

Re-exports all four service classes for convenient import::

    from rag.services import (
        EmbeddingPipelineService,
        RetrievalService,
        IndexingService,
        ContextBuilderService,
    )
"""
from rag.services.embedding_pipeline import EmbeddingPipelineService
from rag.services.retrieval_service import RetrievalService
from rag.services.indexing_service import IndexingService
from rag.services.context_builder import ContextBuilderService

__all__ = [
    "EmbeddingPipelineService",
    "RetrievalService",
    "IndexingService",
    "ContextBuilderService",
]
