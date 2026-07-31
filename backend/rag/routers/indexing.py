"""
RAG Indexing Router — Phase 5.2

FastAPI routes for document ingestion and index management.

Endpoints
---------
POST   /rag/index                                     Ingest one document
POST   /rag/index/batch                               Ingest multiple documents
GET    /rag/index/projects/{project_id}/status        Per-collection index status
DELETE /rag/index/projects/{project_id}               Delete all vectors for a project
DELETE /rag/index/projects/{project_id}/collections/{collection}
                                                      Delete one collection's vectors
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from rag.schemas.indexing import (
    DeleteIndexResponse,
    IndexBatchRequest,
    IndexBatchResult,
    IndexRequest,
    IndexResult,
    IndexStatus,
)
from rag.services.embedding_pipeline import EmbeddingPipelineService
from rag.services.indexing_service import IndexingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["rag-indexing"])


# ── Dependency factories ─────────────────────────────────────────────────────

def _pipeline_service() -> EmbeddingPipelineService:
    """Dependency: return a fresh EmbeddingPipelineService instance."""
    return EmbeddingPipelineService()


def _indexing_service() -> IndexingService:
    """Dependency: return a fresh IndexingService instance."""
    return IndexingService()


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.post(
    "/index",
    response_model=IndexResult,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a document into the RAG vector store",
)
async def index_document(
    body: IndexRequest,
    _user=Depends(get_current_user),
    pipeline: EmbeddingPipelineService = Depends(_pipeline_service),
):
    """
    Chunk, embed, and store a document in the specified ChromaDB collection.

    The document is split using the configured chunk size and overlap,
    embedded via the active provider (Ollama / HuggingFace / Local),
    and persisted in ChromaDB. Returns the memory ID and chunk count.
    """
    try:
        return await pipeline.ingest(body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except RuntimeError as exc:
        logger.error("[RAG-ROUTER] index_document failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post(
    "/index/batch",
    response_model=IndexBatchResult,
    status_code=status.HTTP_201_CREATED,
    summary="Batch ingest multiple documents into the RAG vector store",
)
async def index_batch(
    body: IndexBatchRequest,
    _user=Depends(get_current_user),
    pipeline: EmbeddingPipelineService = Depends(_pipeline_service),
):
    """
    Ingest multiple documents into a single collection in one request.

    Each document is processed independently. Failed documents are counted
    but do not abort the batch. Maximum 50 documents per request.
    """
    from rag.config import rag_settings
    if len(body.documents) > rag_settings.RAG_BATCH_MAX_DOCUMENTS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Batch exceeds maximum of {rag_settings.RAG_BATCH_MAX_DOCUMENTS} documents.",
        )
    try:
        return await pipeline.ingest_batch(body)
    except Exception as exc:
        logger.error("[RAG-ROUTER] index_batch failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get(
    "/index/projects/{project_id}/status",
    response_model=IndexStatus,
    summary="Get vector index status for a project",
)
async def get_index_status(
    project_id: int,
    _user=Depends(get_current_user),
    indexing: IndexingService = Depends(_indexing_service),
):
    """
    Return the number of indexed documents per collection for a project.

    Useful for monitoring index completeness and diagnosing empty search results.
    """
    try:
        return await indexing.get_index_status(project_id)
    except Exception as exc:
        logger.error("[RAG-ROUTER] get_index_status failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.delete(
    "/index/projects/{project_id}",
    response_model=DeleteIndexResponse,
    summary="Delete all vector embeddings for a project",
)
async def delete_project_index(
    project_id: int,
    _user=Depends(get_current_user),
    indexing: IndexingService = Depends(_indexing_service),
):
    """
    Hard-delete all ChromaDB vector embeddings for a project across all collections.

    **Warning:** This operation is irreversible. PostgreSQL persistent memory
    (Phase 5.1) is NOT affected — only the vector index is cleared.
    """
    try:
        return await indexing.delete_project_index(project_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.delete(
    "/index/projects/{project_id}/collections/{collection}",
    response_model=DeleteIndexResponse,
    summary="Delete vector embeddings for a project in a single collection",
)
async def delete_collection_index(
    project_id: int,
    collection: str,
    _user=Depends(get_current_user),
    indexing: IndexingService = Depends(_indexing_service),
):
    """
    Hard-delete ChromaDB embeddings for a project within a specific collection.

    **Warning:** This operation is irreversible.
    """
    try:
        return await indexing.delete_collection_index(project_id, collection)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
