"""
RAG Pipeline package — Phase 3.3.

Public API
----------
from memory.rag import RAGPipeline
from memory.rag import ChunkingEngine, ChunkingConfig, ChunkStrategy
from memory.rag import RetrievalEngine, RetrievalConfig, RetrievalResult
from memory.rag import StorageEngine, StorageConfig, IngestionResult
"""
from memory.rag.schemas import (
    ChunkStrategy,
    ChunkingConfig,
    RetrievalConfig,
    StorageConfig,
    RAGConfig,
    ChunkRecord,
    RetrievalResult,
    IngestionResult,
    MetadataFilter,
    FilterOperator,
)
from memory.rag.chunker import ChunkingEngine
from memory.rag.storage import StorageEngine
from memory.rag.retrieval import RetrievalEngine
from memory.rag.pipeline import RAGPipeline

__all__ = [
    "ChunkStrategy", "ChunkingConfig", "RetrievalConfig", "StorageConfig",
    "RAGConfig", "ChunkRecord", "RetrievalResult", "IngestionResult",
    "MetadataFilter", "FilterOperator",
    "ChunkingEngine", "StorageEngine", "RetrievalEngine", "RAGPipeline",
]
