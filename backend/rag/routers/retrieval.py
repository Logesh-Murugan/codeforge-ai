"""
RAG Retrieval Router — Phase 5.2

FastAPI routes for semantic search, similarity retrieval, context assembly,
document listing, and system health.

Endpoints
---------
POST   /rag/search                                    Multi-collection semantic search
POST   /rag/similar                                   Single-collection similarity search
POST   /rag/context                                   Build agent-ready context block
GET    /rag/projects/{project_id}/documents/{col}     List raw documents in a collection
GET    /rag/health                                    Embedding provider health
GET    /rag/collections                               List available collection names
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from rag.schemas.context import ContextRequest, ContextResponse
from rag.schemas.retrieval import (
    CollectionsResponse,
    HealthResponse,
    ProjectDocumentsResponse,
    SearchRequest,
    SearchResponse,
    SimilarityRequest,
    SimilarityResponse,
)
from rag.services.context_builder import ContextBuilderService
from rag.services.retrieval_service import RetrievalService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["rag-retrieval"])


# ── Dependency factories ─────────────────────────────────────────────────────

def _retrieval_service() -> RetrievalService:
    return RetrievalService()


def _context_service() -> ContextBuilderService:
    return ContextBuilderService()


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Semantic search across one or more RAG collections",
)
async def semantic_search(
    body: SearchRequest,
    _user=Depends(get_current_user),
    retrieval: RetrievalService = Depends(_retrieval_service),
):
    """
    Perform semantic search across one or multiple ChromaDB collections.

    The query is embedded using the active provider (Ollama / HuggingFace / Local).
    Results from all collections are merged and globally ranked by cosine similarity.

    - ``collections``: omit to search all semantic collections (excludes
      'conversation' and 'project_history').
    - ``threshold``: set > 0.0 to filter low-relevance results.
    """
    try:
        return await retrieval.search(body)
    except Exception as exc:
        logger.error("[RAG-ROUTER] semantic_search failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


@router.post(
    "/similar",
    response_model=SimilarityResponse,
    summary="Find similar documents in a single RAG collection",
)
async def find_similar(
    body: SimilarityRequest,
    _user=Depends(get_current_user),
    retrieval: RetrievalService = Depends(_retrieval_service),
):
    """
    Find documents semantically similar to the query within a single named collection.

    Use this when you know which collection to search (e.g. 'backend_code').
    For cross-collection search, use the ``/rag/search`` endpoint instead.
    """
    try:
        return await retrieval.find_similar(body)
    except Exception as exc:
        logger.error("[RAG-ROUTER] find_similar failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


@router.post(
    "/context",
    response_model=ContextResponse,
    summary="Build an agent-ready context block from project memory",
)
async def build_context(
    body: ContextRequest,
    _user=Depends(get_current_user),
    ctx_service: ContextBuilderService = Depends(_context_service),
):
    """
    Assemble a prompt-ready context block for agent injection.

    Searches multiple collections, globally ranks chunks by similarity,
    applies a character budget, and formats a structured ``context_text``
    string ready to be prepended to any agent prompt.

    Optionally includes recent conversation history when
    ``include_conversation=true``.
    """
    try:
        return await ctx_service.build_context(body)
    except Exception as exc:
        logger.error("[RAG-ROUTER] build_context failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


@router.get(
    "/projects/{project_id}/documents/{collection}",
    response_model=ProjectDocumentsResponse,
    summary="List all raw documents stored for a project in a collection",
)
async def get_project_documents(
    project_id: int,
    collection: str,
    _user=Depends(get_current_user),
    retrieval: RetrievalService = Depends(_retrieval_service),
):
    """
    Return all raw documents stored for a project in the specified collection.

    Useful for inspecting indexed content without performing a search query.
    """
    from rag.config import rag_settings
    if collection not in rag_settings.get_collections():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown collection '{collection}'.",
        )
    try:
        return await retrieval.get_project_documents(project_id, collection)
    except Exception as exc:
        logger.error("[RAG-ROUTER] get_project_documents failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="RAG engine health — active embedding provider status",
)
async def rag_health(
    _user=Depends(get_current_user),
    retrieval: RetrievalService = Depends(_retrieval_service),
):
    """
    Report the active embedding provider, its mode (local/cloud/fallback),
    vector dimension, and health check result.

    - **local** — Ollama running locally with `nomic-embed-text`
    - **cloud** — HuggingFace Inference API (`all-MiniLM-L6-v2` etc.)
    - **fallback** — LocalEmbeddings (hash-projection, always available)
    """
    try:
        return await retrieval.get_provider_health()
    except Exception as exc:
        logger.error("[RAG-ROUTER] rag_health failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


@router.get(
    "/collections",
    response_model=CollectionsResponse,
    summary="List all available RAG collection names",
)
async def list_collections(
    _user=Depends(get_current_user),
    retrieval: RetrievalService = Depends(_retrieval_service),
):
    """Return the list of all registered ChromaDB collection names."""
    return await retrieval.get_collections()
