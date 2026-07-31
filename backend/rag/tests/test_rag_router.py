"""
Tests for Phase 5.2 — RAG Routers (API Tests)

Tests all 11 RAG endpoints using FastAPI TestClient with mocked
service dependencies.  No live DB, ChromaDB, or Ollama required.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from rag.routers.indexing import router as indexing_router
from rag.routers.retrieval import router as retrieval_router


# ── App fixture with auth override ───────────────────────────────────────────

def _fake_user():
    return {"id": 1, "email": "test@test.com"}


@pytest.fixture
def client():
    """TestClient with both RAG routers and auth dependency overridden."""
    from app.core.security import get_current_user

    app = FastAPI()
    app.include_router(indexing_router)
    app.include_router(retrieval_router)
    app.dependency_overrides[get_current_user] = lambda: _fake_user()
    return TestClient(app)


# ── Mock builder helpers ──────────────────────────────────────────────────────

def _mock_index_result():
    from rag.schemas.indexing import IndexResult
    return IndexResult(
        memory_id="test-uuid-0001",
        chunks_stored=2,
        collection="requirements",
        project_id=42,
        artifact_type="requirements",
        indexed_at=datetime.now(timezone.utc),
    )


def _mock_batch_result():
    from rag.schemas.indexing import IndexBatchResult
    return IndexBatchResult(
        project_id=42,
        collection="requirements",
        total_documents=2,
        total_chunks=4,
        results=[_mock_index_result(), _mock_index_result()],
        failed=0,
        indexed_at=datetime.now(timezone.utc),
    )


def _mock_index_status():
    from rag.schemas.indexing import IndexStatus
    return IndexStatus(
        project_id=42,
        collections={"requirements": 5, "architecture": 3},
        total_documents=8,
    )


def _mock_delete_response(collection=None):
    from rag.schemas.indexing import DeleteIndexResponse
    return DeleteIndexResponse(
        message="Deleted successfully.",
        project_id=42,
        collection=collection,
    )


def _mock_search_response():
    from rag.schemas.retrieval import SearchResponse, SearchResult
    return SearchResponse(
        project_id=42,
        query="auth requirements",
        results=[
            SearchResult(
                id="uuid-1",
                document="JWT is used for authentication.",
                metadata={},
                similarity_score=0.92,
                collection="requirements",
            )
        ],
        total=1,
        collections_searched=["requirements"],
    )


def _mock_similarity_response():
    from rag.schemas.retrieval import SimilarityResponse, SimilarityResult
    return SimilarityResponse(
        project_id=42,
        query="database schema",
        collection="database_design",
        results=[
            SimilarityResult(
                id="uuid-2",
                document="The schema has a users table.",
                metadata={},
                similarity_score=0.88,
                collection="database_design",
            )
        ],
        total=1,
    )


def _mock_context_response():
    from rag.schemas.context import (
        ContextBlock, ContextChunk, ContextResponse,
    )
    chunk = ContextChunk(
        content="JWT is used for authentication.",
        source_collection="requirements",
        similarity_score=0.92,
        metadata={},
    )
    block = ContextBlock(
        project_id=42,
        agent_name="backend_agent",
        query="authentication flow",
        chunks=[chunk],
        conversation_history=[],
        context_text="# Context for backend_agent\n## Query: authentication flow\n",
        total_chunks=1,
        collections_searched=["requirements"],
        built_at=datetime.now(timezone.utc),
    )
    return ContextResponse(
        project_id=42,
        agent_name="backend_agent",
        query="authentication flow",
        context=block,
        total_chunks=1,
        collections_searched=["requirements"],
    )


def _mock_project_documents_response():
    from rag.schemas.retrieval import ProjectDocumentsResponse, DocumentRecord
    return ProjectDocumentsResponse(
        project_id=42,
        collection="requirements",
        documents=[
            DocumentRecord(
                id="doc-1",
                document="Raw document text.",
                metadata={},
                collection="requirements",
            )
        ],
        total=1,
    )


def _mock_health_response():
    from rag.schemas.retrieval import HealthResponse
    return HealthResponse(
        status="healthy",
        embedding_provider="ollama",
        embedding_dimension=768,
        provider_healthy=True,
        mode="local",
    )


def _mock_collections_response():
    from rag.schemas.retrieval import CollectionsResponse
    return CollectionsResponse(
        collections=["requirements", "backend_code"],
        total=2,
    )


# ── Indexing router tests ─────────────────────────────────────────────────────

class TestIndexEndpoint:
    """Tests for POST /rag/index."""

    def test_index_document_success(self, client):
        """Valid request returns 201 with IndexResult."""
        with patch(
            "rag.routers.indexing.EmbeddingPipelineService.ingest",
            new=AsyncMock(return_value=_mock_index_result()),
        ):
            resp = client.post(
                "/rag/index",
                json={
                    "project_id": 42,
                    "collection": "requirements",
                    "content": "JWT authentication is required.",
                    "artifact_type": "requirements",
                    "agent_name": "system",
                    "version": 1,
                },
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["memory_id"] == "test-uuid-0001"
        assert data["chunks_stored"] == 2

    def test_index_document_empty_content_returns_422(self, client):
        """Empty content triggers validation error."""
        resp = client.post(
            "/rag/index",
            json={
                "project_id": 42,
                "collection": "requirements",
                "content": "",
            },
        )
        assert resp.status_code == 422

    def test_index_document_missing_project_id_returns_422(self, client):
        """Missing required field returns 422."""
        resp = client.post(
            "/rag/index",
            json={"collection": "requirements", "content": "some content"},
        )
        assert resp.status_code == 422

    def test_index_document_runtime_error_returns_500(self, client):
        """RuntimeError from service returns 500."""
        with patch(
            "rag.routers.indexing.EmbeddingPipelineService.ingest",
            new=AsyncMock(side_effect=RuntimeError("Embedding failure")),
        ):
            resp = client.post(
                "/rag/index",
                json={
                    "project_id": 42,
                    "collection": "requirements",
                    "content": "Some content",
                },
            )
        assert resp.status_code == 500


class TestIndexBatchEndpoint:
    """Tests for POST /rag/index/batch."""

    def test_batch_success(self, client):
        """Valid batch returns 201 with IndexBatchResult."""
        with patch(
            "rag.routers.indexing.EmbeddingPipelineService.ingest_batch",
            new=AsyncMock(return_value=_mock_batch_result()),
        ):
            resp = client.post(
                "/rag/index/batch",
                json={
                    "project_id": 42,
                    "collection": "requirements",
                    "documents": [
                        {"content": "Doc 1", "artifact_type": "requirements"},
                        {"content": "Doc 2", "artifact_type": "requirements"},
                    ],
                },
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["total_documents"] == 2

    def test_batch_no_documents_returns_422(self, client):
        """Empty documents array fails validation."""
        resp = client.post(
            "/rag/index/batch",
            json={
                "project_id": 42,
                "collection": "requirements",
                "documents": [],
            },
        )
        assert resp.status_code == 422


class TestIndexStatusEndpoint:
    """Tests for GET /rag/index/projects/{project_id}/status."""

    def test_get_status_success(self, client):
        """Returns 200 with IndexStatus."""
        with patch(
            "rag.routers.indexing.IndexingService.get_index_status",
            new=AsyncMock(return_value=_mock_index_status()),
        ):
            resp = client.get("/rag/index/projects/42/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == 42
        assert data["total_documents"] == 8


class TestDeleteProjectIndexEndpoint:
    """Tests for DELETE /rag/index/projects/{project_id}."""

    def test_delete_project_success(self, client):
        """Returns 200 with DeleteIndexResponse."""
        with patch(
            "rag.routers.indexing.IndexingService.delete_project_index",
            new=AsyncMock(return_value=_mock_delete_response()),
        ):
            resp = client.delete("/rag/index/projects/42")
        assert resp.status_code == 200
        assert "Deleted successfully" in resp.json()["message"]


class TestDeleteCollectionIndexEndpoint:
    """Tests for DELETE /rag/index/projects/{project_id}/collections/{collection}."""

    def test_delete_collection_success(self, client):
        """Returns 200 with DeleteIndexResponse."""
        with patch(
            "rag.routers.indexing.IndexingService.delete_collection_index",
            new=AsyncMock(return_value=_mock_delete_response("requirements")),
        ):
            resp = client.delete("/rag/index/projects/42/collections/requirements")
        assert resp.status_code == 200
        assert resp.json()["collection"] == "requirements"

    def test_delete_unknown_collection_returns_404(self, client):
        """ValueError from service returns 404."""
        with patch(
            "rag.routers.indexing.IndexingService.delete_collection_index",
            new=AsyncMock(side_effect=ValueError("Unknown collection 'bogus'")),
        ):
            resp = client.delete("/rag/index/projects/42/collections/bogus")
        assert resp.status_code == 404


# ── Retrieval router tests ────────────────────────────────────────────────────

class TestSearchEndpoint:
    """Tests for POST /rag/search."""

    def test_search_success(self, client):
        """Valid request returns 200 with SearchResponse."""
        with patch(
            "rag.routers.retrieval.RetrievalService.search",
            new=AsyncMock(return_value=_mock_search_response()),
        ):
            resp = client.post(
                "/rag/search",
                json={
                    "project_id": 42,
                    "query": "auth requirements",
                    "collections": ["requirements"],
                    "limit": 5,
                },
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["results"][0]["similarity_score"] == 0.92

    def test_search_empty_query_returns_422(self, client):
        """Empty query string fails validation."""
        resp = client.post(
            "/rag/search",
            json={"project_id": 42, "query": ""},
        )
        assert resp.status_code == 422


class TestSimilarityEndpoint:
    """Tests for POST /rag/similar."""

    def test_similarity_success(self, client):
        """Valid request returns 200 with SimilarityResponse."""
        with patch(
            "rag.routers.retrieval.RetrievalService.find_similar",
            new=AsyncMock(return_value=_mock_similarity_response()),
        ):
            resp = client.post(
                "/rag/similar",
                json={
                    "project_id": 42,
                    "query": "database schema",
                    "collection": "database_design",
                    "limit": 5,
                },
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["collection"] == "database_design"


class TestContextEndpoint:
    """Tests for POST /rag/context."""

    def test_context_success(self, client):
        """Valid request returns 200 with ContextResponse."""
        with patch(
            "rag.routers.retrieval.ContextBuilderService.build_context",
            new=AsyncMock(return_value=_mock_context_response()),
        ):
            resp = client.post(
                "/rag/context",
                json={
                    "project_id": 42,
                    "agent_name": "backend_agent",
                    "query": "authentication flow",
                    "limit": 5,
                },
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["agent_name"] == "backend_agent"
        assert "context_text" in data["context"]

    def test_context_empty_query_returns_422(self, client):
        """Empty query fails validation."""
        resp = client.post(
            "/rag/context",
            json={"project_id": 42, "agent_name": "agent", "query": ""},
        )
        assert resp.status_code == 422


class TestDocumentsEndpoint:
    """Tests for GET /rag/projects/{project_id}/documents/{collection}."""

    def test_get_documents_success(self, client):
        """Valid request returns 200 with ProjectDocumentsResponse."""
        with patch(
            "rag.routers.retrieval.RetrievalService.get_project_documents",
            new=AsyncMock(return_value=_mock_project_documents_response()),
        ):
            resp = client.get("/rag/projects/42/documents/requirements")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1

    def test_get_documents_unknown_collection_returns_404(self, client):
        """Unknown collection returns 404."""
        resp = client.get("/rag/projects/42/documents/nonexistent_collection")
        assert resp.status_code == 404


class TestHealthEndpoint:
    """Tests for GET /rag/health."""

    def test_health_success(self, client):
        """Returns 200 with HealthResponse."""
        with patch(
            "rag.routers.retrieval.RetrievalService.get_provider_health",
            new=AsyncMock(return_value=_mock_health_response()),
        ):
            resp = client.get("/rag/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["embedding_provider"] == "ollama"
        assert data["mode"] == "local"


class TestCollectionsEndpoint:
    """Tests for GET /rag/collections."""

    def test_collections_success(self, client):
        """Returns 200 with CollectionsResponse."""
        with patch(
            "rag.routers.retrieval.RetrievalService.get_collections",
            new=AsyncMock(return_value=_mock_collections_response()),
        ):
            resp = client.get("/rag/collections")
        assert resp.status_code == 200
        data = resp.json()
        assert "requirements" in data["collections"]
