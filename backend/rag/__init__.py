"""
RAG Engine — Phase 5.2

Retrieval-Augmented Generation pipeline for CodeForge AI.

Sub-packages:
    rag.schemas      — Pydantic data contracts (indexing, retrieval, context)
    rag.services     — Business logic (embedding pipeline, retrieval, context)
    rag.routers      — FastAPI route handlers
    rag.tests        — Unit and integration tests

Embedding modes (auto-resolved at runtime):
    LOCAL  — Ollama + nomic-embed-text  (EMBEDDING_PROVIDER=ollama)
    CLOUD  — HuggingFace Inference API  (EMBEDDING_PROVIDER=huggingface)
    FALLBACK — LocalEmbeddings (hash-projection, always available)

Usage::

    from rag.services import EmbeddingPipelineService, RetrievalService
    from rag.routers.indexing import router as rag_index_router
    from rag.routers.retrieval import router as rag_retrieval_router
"""
__version__ = "5.2.0"
