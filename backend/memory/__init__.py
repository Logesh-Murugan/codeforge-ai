"""
CodeForge AI — Memory Subsystem
================================

This is the public API surface of the memory package.  Import from here
to avoid coupling to internal module paths.

Quick-start
-----------
    # Auto-wired service (reads env-vars for provider selection):
    from memory import get_service
    service = get_service()

    # Store an artifact:
    service.store_memory(
        project_id=1,
        agent_name="backend_developer",
        artifact_type="python_code",
        collection_name="backend_code",
        content="...",
        version=1,
    )

    # Semantic search:
    results = service.retrieve_memory(
        project_id=1,
        collection_name="backend_code",
        query="FastAPI authentication",
    )

    # Context injection for an agent prompt:
    context = service.build_agent_context(
        project_id=1,
        agent_name="code_reviewer",
        query="security authentication",
    )
    prompt += context.to_prompt_block()

Architecture layers
-------------------
    memory/
    ├── interfaces/         Abstract contracts (no SDK imports)
    │   ├── embedding.py    EmbeddingProviderInterface
    │   ├── vectorstore.py  VectorStoreInterface
    │   └── memory.py       MemoryProviderInterface
    ├── embeddings/         Concrete embedding providers
    │   ├── local.py        Hash-projection (zero-dependency fallback)
    │   ├── ollama.py       Ollama REST API (nomic-embed-text, local)
    │   ├── huggingface.py  HuggingFace Inference API (cloud)
    │   └── resolver.py     Configuration-driven provider selection
    ├── vectorstores/       Concrete vector store backends
    │   └── chroma.py       ChromaDB persistent store
    ├── utils/              Pure-Python helpers
    │   ├── similarity.py   Cosine similarity + re-ranking
    │   ├── chunking.py     Text chunking for the RAG pipeline
    │   └── cache.py        LRU embedding cache wrapper
    ├── schemas.py          Pydantic data contracts
    ├── config.py           MemorySettings (env-var driven)
    ├── service.py          MemoryService — full pipeline façade
    └── manager.py          MemoryManager — wiring + lifecycle
"""
from memory.interfaces import (
    EmbeddingProviderInterface,
    MemoryProviderInterface,
    VectorStoreInterface,
)
from memory.schemas import (
    AgentContext,
    ArtifactType,
    CollectionName,
    EmbeddingProviderName,
    MemoryMetadata,
    MemoryMode,
    MemoryQuery,
    MemoryQueryResult,
    MemoryRecord,
    MemoryStoreRequest,
    ProjectHistoryEntry,
    ProviderHealth,
    TextChunk,
    # Phase 3.4
    AgentMemoryRecord,
    GeneratedFileRecord,
    RevisionEntry,
    ProjectSnapshot,
    StoreArtifactRequest,
    StoreRevisionRequest,
    VersionHistoryQuery,
    MemorySearchRequest,
)
from memory.project_memory import ProjectMemoryService
from memory.cache import MemoryCache
from memory.performance import PerformanceMonitor
from memory.context import (
    ContextInjector,
    AgentRole,
    AGENT_ROLES,
    CrossAgentMemory,
    LongTermMemory,
    ConversationMemory,
)
from memory.embeddings import (
    LocalEmbeddings,
    OllamaEmbeddings,
    HuggingFaceEmbeddings,
    resolve_provider,
)
from memory.vectorstores import ChromaVectorStore
from memory.utils import (
    cosine_similarity,
    rank_results,
    chunk_text,
    chunk_documents,
    CachedEmbeddingProvider,
)
from memory.service import MemoryService
from memory.manager import MemoryManager, default_manager
from memory.rag import (
    RAGPipeline,
    ChunkingEngine, ChunkingConfig, ChunkStrategy,
    RetrievalEngine, RetrievalConfig, RetrievalResult,
    StorageEngine, StorageConfig, IngestionResult,
    RAGConfig, MetadataFilter, FilterOperator, ChunkRecord,
)


def get_service() -> MemoryService:
    """
    Return the default, auto-configured MemoryService.

    Provider selection follows the EMBEDDING_PROVIDER /
    EMBEDDING_FALLBACK_CHAIN environment variables.  The result is
    cached on the module-level ``default_manager``.
    """
    return default_manager.get_service()


__all__ = [
    # Interfaces
    "EmbeddingProviderInterface",
    "MemoryProviderInterface",
    "VectorStoreInterface",
    # Schemas (core)
    "AgentContext",
    "ArtifactType",
    "CollectionName",
    "EmbeddingProviderName",
    "MemoryMetadata",
    "MemoryMode",
    "MemoryQuery",
    "MemoryQueryResult",
    "MemoryRecord",
    "MemoryStoreRequest",
    "ProjectHistoryEntry",
    "ProviderHealth",
    "TextChunk",
    # Schemas (Phase 3.4)
    "AgentMemoryRecord",
    "GeneratedFileRecord",
    "RevisionEntry",
    "ProjectSnapshot",
    "StoreArtifactRequest",
    "StoreRevisionRequest",
    "VersionHistoryQuery",
    "MemorySearchRequest",
    # Embedding providers
    "LocalEmbeddings",
    "OllamaEmbeddings",
    "HuggingFaceEmbeddings",
    "resolve_provider",
    # Vector stores
    "ChromaVectorStore",
    # Utils
    "cosine_similarity",
    "rank_results",
    "chunk_text",
    "chunk_documents",
    "CachedEmbeddingProvider",
    # Service + manager
    "MemoryService",
    "MemoryManager",
    "default_manager",
    "get_service",
    # Phase 3.4
    "ProjectMemoryService",
    # Phase 3.5 — Agent Context Sharing
    "ContextInjector",
    "AgentRole",
    "AGENT_ROLES",
    "CrossAgentMemory",
    "LongTermMemory",
    "ConversationMemory",
    # Phase 3.6 — Production Hardening
    "MemoryCache",
    "PerformanceMonitor",
]
