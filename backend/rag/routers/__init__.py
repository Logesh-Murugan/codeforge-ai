"""
RAG routers package — Phase 5.2

Re-exports both routers for convenience::

    from rag.routers.indexing import router as rag_index_router
    from rag.routers.retrieval import router as rag_retrieval_router
"""
from rag.routers.indexing import router as rag_index_router
from rag.routers.retrieval import router as rag_retrieval_router

__all__ = ["rag_index_router", "rag_retrieval_router"]
