"""
Tests for Phase 5.2 — RetrievalService (Unit Tests)

All tests use a mocked MemoryService — no live DB, Ollama, or ChromaDB required.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from rag.schemas.retrieval import SearchRequest, SimilarityRequest
from rag.services.retrieval_service import RetrievalService


# ── Fixtures ─────────────────────────────────────────────────────────────────

def _raw_result(doc: str = "test doc", score: float = 0.9, col: str = "requirements"):
    return {
        "id": "uuid-1234",
        "document": doc,
        "metadata": {
            "project_id": 42,
            "artifact_type": "requirements",
            "agent_name": "system",
        },
        "similarity_score": score,
    }


def _make_mock_service(results=None):
    svc = MagicMock()
    svc.retrieve_memory.return_value = results if results is not None else [_raw_result()]
    svc.get_project_memory.return_value = [
        {"id": "doc-1", "document": "raw doc text", "metadata": {"artifact_type": "requirements"}}
    ]
    return svc


def _make_search_request(**kwargs):
    defaults = {
        "project_id": 42,
        "query": "authentication requirements",
        "collections": ["requirements"],
        "limit": 5,
        "threshold": 0.0,
    }
    defaults.update(kwargs)
    return SearchRequest(**defaults)


def _make_similarity_request(**kwargs):
    defaults = {
        "project_id": 42,
        "query": "database schema",
        "collection": "database_design",
        "limit": 5,
        "threshold": 0.0,
    }
    defaults.update(kwargs)
    return SimilarityRequest(**defaults)


# ── RetrievalService — search ─────────────────────────────────────────────────

class TestSearch:
    """Tests for RetrievalService.search()."""

    @pytest.mark.asyncio
    async def test_search_returns_results(self):
        """Search returns a SearchResponse with matching results."""
        svc = RetrievalService(memory_service=_make_mock_service())
        resp = await svc.search(_make_search_request())

        assert resp.project_id == 42
        assert resp.query == "authentication requirements"
        assert resp.total >= 1
        assert len(resp.results) >= 1

    @pytest.mark.asyncio
    async def test_search_result_has_collection_field(self):
        """Each SearchResult includes the source collection name."""
        svc = RetrievalService(memory_service=_make_mock_service())
        resp = await svc.search(_make_search_request(collections=["requirements"]))

        for result in resp.results:
            assert result.collection == "requirements"

    @pytest.mark.asyncio
    async def test_search_collections_searched_field(self):
        """SearchResponse.collections_searched echoes the queried collections."""
        svc = RetrievalService(memory_service=_make_mock_service())
        req = _make_search_request(collections=["requirements", "architecture"])
        resp = await svc.search(req)

        assert "requirements" in resp.collections_searched
        assert "architecture" in resp.collections_searched

    @pytest.mark.asyncio
    async def test_search_deduplicates_by_id(self):
        """Results with the same document ID are deduplicated."""
        duplicate = _raw_result()
        mock_svc = MagicMock()
        mock_svc.retrieve_memory.return_value = [duplicate, duplicate]
        svc = RetrievalService(memory_service=mock_svc)
        req = _make_search_request(collections=["requirements"])

        resp = await svc.search(req)

        ids = [r.id for r in resp.results]
        assert len(ids) == len(set(ids))

    @pytest.mark.asyncio
    async def test_search_empty_results_when_service_returns_empty(self):
        """SearchResponse with zero results is valid."""
        svc = RetrievalService(memory_service=_make_mock_service(results=[]))
        resp = await svc.search(_make_search_request())

        assert resp.total == 0
        assert resp.results == []

    @pytest.mark.asyncio
    async def test_search_skips_failing_collection(self):
        """A collection that raises an exception is skipped gracefully."""
        mock_svc = MagicMock()
        mock_svc.retrieve_memory.side_effect = RuntimeError("ChromaDB unavailable")
        svc = RetrievalService(memory_service=mock_svc)
        resp = await svc.search(_make_search_request(collections=["requirements"]))

        assert resp.total == 0  # gracefully returns empty

    @pytest.mark.asyncio
    async def test_search_results_sorted_by_similarity_desc(self):
        """Results are sorted from highest to lowest similarity."""
        raw = [
            _raw_result(score=0.5),
            _raw_result(score=0.9),
            _raw_result(score=0.3),
        ]
        # Give unique ids
        for i, r in enumerate(raw):
            r["id"] = f"id-{i}"
        svc = RetrievalService(memory_service=_make_mock_service(results=raw))
        resp = await svc.search(_make_search_request(collections=["requirements"]))

        scores = [r.similarity_score for r in resp.results]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_search_defaults_to_semantic_collections(self):
        """When no collections specified, uses all semantic (non-meta) collections."""
        mock_svc = _make_mock_service(results=[])
        svc = RetrievalService(memory_service=mock_svc)
        req = _make_search_request(collections=None)
        resp = await svc.search(req)

        # conversation and project_history should be excluded
        assert "conversation" not in resp.collections_searched
        assert "project_history" not in resp.collections_searched


# ── RetrievalService — find_similar ──────────────────────────────────────────

class TestFindSimilar:
    """Tests for RetrievalService.find_similar()."""

    @pytest.mark.asyncio
    async def test_find_similar_returns_results(self):
        """find_similar returns a SimilarityResponse with results."""
        svc = RetrievalService(memory_service=_make_mock_service())
        resp = await svc.find_similar(_make_similarity_request())

        assert resp.project_id == 42
        assert resp.collection == "database_design"
        assert resp.total >= 1

    @pytest.mark.asyncio
    async def test_find_similar_calls_retrieve_memory(self):
        """retrieve_memory is called with the correct collection."""
        mock_svc = _make_mock_service()
        svc = RetrievalService(memory_service=mock_svc)
        await svc.find_similar(_make_similarity_request(collection="backend_code"))

        mock_svc.retrieve_memory.assert_called_once()
        call_kwargs = mock_svc.retrieve_memory.call_args.kwargs
        assert call_kwargs["collection_name"] == "backend_code"

    @pytest.mark.asyncio
    async def test_find_similar_returns_empty_on_failure(self):
        """Returns empty list gracefully when ChromaDB fails."""
        mock_svc = MagicMock()
        mock_svc.retrieve_memory.side_effect = RuntimeError("Failure")
        svc = RetrievalService(memory_service=mock_svc)
        resp = await svc.find_similar(_make_similarity_request())

        assert resp.total == 0
        assert resp.results == []


# ── RetrievalService — get_project_documents ─────────────────────────────────

class TestGetProjectDocuments:
    """Tests for RetrievalService.get_project_documents()."""

    @pytest.mark.asyncio
    async def test_returns_documents(self):
        """get_project_documents returns all raw docs for a project."""
        svc = RetrievalService(memory_service=_make_mock_service())
        resp = await svc.get_project_documents(42, "requirements")

        assert resp.project_id == 42
        assert resp.collection == "requirements"
        assert resp.total == 1
        assert len(resp.documents) == 1

    @pytest.mark.asyncio
    async def test_returns_empty_on_failure(self):
        """Returns empty response when underlying service fails."""
        mock_svc = MagicMock()
        mock_svc.get_project_memory.side_effect = RuntimeError("Store error")
        svc = RetrievalService(memory_service=mock_svc)
        resp = await svc.get_project_documents(42, "requirements")

        assert resp.total == 0
        assert resp.documents == []


# ── RetrievalService — get_collections ───────────────────────────────────────

class TestGetCollections:
    """Tests for RetrievalService.get_collections()."""

    @pytest.mark.asyncio
    async def test_returns_all_known_collections(self):
        """get_collections returns all registered collection names."""
        svc = RetrievalService(memory_service=MagicMock())
        resp = await svc.get_collections()

        assert resp.total > 0
        assert "requirements" in resp.collections
        assert "backend_code" in resp.collections
        assert "documentation" in resp.collections


# ── RetrievalService — get_provider_health ───────────────────────────────────

class TestProviderHealth:
    """Tests for RetrievalService.get_provider_health()."""

    @pytest.mark.asyncio
    async def test_health_returns_response(self):
        """get_provider_health always returns a HealthResponse."""
        from memory.schemas import ProviderHealth

        mock_health = ProviderHealth(
            provider_name="local",
            healthy=True,
            dimension=1536,
        )

        mock_manager = MagicMock()
        mock_manager.health_check.return_value = mock_health
        mock_provider = MagicMock()
        mock_provider.dimension = 1536
        mock_manager.get_embedding_provider.return_value = mock_provider

        # default_manager is lazily imported inside get_provider_health;
        # patch at the source module (memory.manager) where it lives.
        with patch("memory.manager.default_manager", mock_manager):
            svc = RetrievalService()
            resp = await svc.get_provider_health()

        assert resp.status in ("healthy", "degraded")
        assert resp.embedding_provider == "local"
        assert resp.embedding_dimension == 1536

    @pytest.mark.asyncio
    async def test_health_returns_degraded_on_exception(self):
        """Returns degraded status when health check raises."""
        mock_manager = MagicMock()
        mock_manager.health_check.side_effect = RuntimeError("No provider")

        with patch("memory.manager.default_manager", mock_manager):
            svc = RetrievalService()
            resp = await svc.get_provider_health()

        assert resp.status == "degraded"
        assert resp.provider_healthy is False
