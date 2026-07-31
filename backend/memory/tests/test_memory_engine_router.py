"""
Tests for Phase 5.1 — Memory Engine Router (API Tests)

Tests the ``/memory-engine`` FastAPI router with mocked engine
dependencies.  No database or network required.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from memory.routers.memory_engine import router


# ── Fixtures ────────────────────────────────────────────────────────────────

def _fake_user():
    """Return a fake user for auth override."""
    return {"id": 1, "email": "test@test.com"}


@pytest.fixture
def client():
    """TestClient with auth dependency overridden."""
    from app.core.security import get_current_user

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: _fake_user()
    return TestClient(app)


@pytest.fixture
def unauth_client():
    """TestClient without auth override (should fail)."""
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _mock_response(**kwargs):
    """Build a dict that matches PersistentMemoryResponse."""
    now = datetime.now(timezone.utc).isoformat()
    base = {
        "id": 1, "project_id": 42, "category": "project",
        "agent_name": "system", "content": "Test",
        "metadata_json": {}, "version": 1, "is_active": True,
        "created_at": now, "updated_at": now,
    }
    base.update(kwargs)
    return base


# ── Auth Tests ──────────────────────────────────────────────────────────────


class TestMemoryEngineRouterAuth:
    """All endpoints must require authentication."""

    def test_list_domains_requires_auth(self, unauth_client):
        resp = unauth_client.get("/memory-engine/domains")
        assert resp.status_code in (401, 403)

    def test_create_requires_auth(self, unauth_client):
        resp = unauth_client.post(
            "/memory-engine/project/projects/1/entries",
            json={"content": "test"},
        )
        assert resp.status_code in (401, 403)

    def test_list_requires_auth(self, unauth_client):
        resp = unauth_client.get("/memory-engine/project/projects/1/entries")
        assert resp.status_code in (401, 403)

    def test_get_requires_auth(self, unauth_client):
        resp = unauth_client.get("/memory-engine/project/projects/1/entries/1")
        assert resp.status_code in (401, 403)

    def test_update_requires_auth(self, unauth_client):
        resp = unauth_client.put(
            "/memory-engine/project/projects/1/entries/1",
            json={"content": "updated"},
        )
        assert resp.status_code in (401, 403)

    def test_delete_requires_auth(self, unauth_client):
        resp = unauth_client.delete(
            "/memory-engine/project/projects/1/entries/1",
        )
        assert resp.status_code in (401, 403)

    def test_search_requires_auth(self, unauth_client):
        resp = unauth_client.post(
            "/memory-engine/project/projects/1/search",
            json={"query": "test"},
        )
        assert resp.status_code in (401, 403)

    def test_versions_requires_auth(self, unauth_client):
        resp = unauth_client.get(
            "/memory-engine/project/projects/1/entries/1/versions",
        )
        assert resp.status_code in (401, 403)

    def test_similar_requires_auth(self, unauth_client):
        resp = unauth_client.post(
            "/memory-engine/project/projects/1/similar",
            json={"query": "test"},
        )
        assert resp.status_code in (401, 403)

    def test_summary_requires_auth(self, unauth_client):
        resp = unauth_client.get(
            "/memory-engine/project/projects/1/summary",
        )
        assert resp.status_code in (401, 403)


# ── Domain Resolution Tests ────────────────────────────────────────────────


class TestMemoryEngineRouterDomains:
    """Test domain path parameter resolution."""

    def test_list_domains(self, client):
        resp = client.get("/memory-engine/domains")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 12
        assert "project" in data["domains"]
        assert "security" in data["domains"]

    @patch("memory.routers.memory_engine.get_engine")
    def test_invalid_domain_returns_404(self, mock_get, client):
        from memory.routers.memory_engine import get_engine as real_get
        mock_get.side_effect = ValueError("Unknown memory domain 'invalid'")
        resp = client.get("/memory-engine/invalid/projects/1/entries")
        assert resp.status_code == 404


# ── CRUD Endpoint Tests ─────────────────────────────────────────────────────


class TestMemoryEngineRouterCRUD:
    """Test CRUD endpoints with mocked engines."""

    @patch("memory.routers.memory_engine.get_engine")
    def test_create_entry(self, mock_get, client):
        mock_engine = MagicMock()
        mock_engine.create = AsyncMock(return_value=MagicMock(
            **_mock_response(content="New entry"),
            model_dump=lambda **kw: _mock_response(content="New entry"),
        ))
        mock_get.return_value = mock_engine

        resp = client.post(
            "/memory-engine/project/projects/42/entries",
            json={"content": "New entry"},
        )
        assert resp.status_code == 201

    @patch("memory.routers.memory_engine.get_engine")
    def test_list_entries(self, mock_get, client):
        mock_entry = MagicMock()
        for k, v in _mock_response().items():
            setattr(mock_entry, k, v)
        mock_entry.model_dump = lambda **kw: _mock_response()

        mock_engine = MagicMock()
        mock_engine.list_entries = AsyncMock(return_value=[mock_entry])
        mock_get.return_value = mock_engine

        resp = client.get("/memory-engine/project/projects/42/entries")
        assert resp.status_code == 200
        data = resp.json()
        assert data["domain"] == "project"
        assert data["total"] >= 1

    @patch("memory.routers.memory_engine.get_engine")
    def test_get_entry(self, mock_get, client):
        mock_entry = MagicMock()
        for k, v in _mock_response().items():
            setattr(mock_entry, k, v)
        mock_entry.model_dump = lambda **kw: _mock_response()

        mock_engine = MagicMock()
        mock_engine.get = AsyncMock(return_value=mock_entry)
        mock_get.return_value = mock_engine

        resp = client.get("/memory-engine/project/projects/42/entries/1")
        assert resp.status_code == 200

    @patch("memory.routers.memory_engine.get_engine")
    def test_get_entry_not_found(self, mock_get, client):
        mock_engine = MagicMock()
        mock_engine.get = AsyncMock(return_value=None)
        mock_get.return_value = mock_engine

        resp = client.get("/memory-engine/project/projects/42/entries/999")
        assert resp.status_code == 404

    @patch("memory.routers.memory_engine.get_engine")
    def test_update_entry(self, mock_get, client):
        mock_entry = MagicMock()
        for k, v in _mock_response(version=2).items():
            setattr(mock_entry, k, v)
        mock_entry.model_dump = lambda **kw: _mock_response(version=2)

        mock_engine = MagicMock()
        mock_engine.update = AsyncMock(return_value=mock_entry)
        mock_get.return_value = mock_engine

        resp = client.put(
            "/memory-engine/project/projects/42/entries/1",
            json={"content": "Updated"},
        )
        assert resp.status_code == 200

    @patch("memory.routers.memory_engine.get_engine")
    def test_update_not_found(self, mock_get, client):
        mock_engine = MagicMock()
        mock_engine.update = AsyncMock(return_value=None)
        mock_get.return_value = mock_engine

        resp = client.put(
            "/memory-engine/project/projects/42/entries/999",
            json={"content": "Updated"},
        )
        assert resp.status_code == 404

    @patch("memory.routers.memory_engine.get_engine")
    def test_delete_entry(self, mock_get, client):
        mock_engine = MagicMock()
        mock_engine.delete = AsyncMock(return_value=True)
        mock_get.return_value = mock_engine

        resp = client.delete("/memory-engine/project/projects/42/entries/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["domain"] == "project"

    @patch("memory.routers.memory_engine.get_engine")
    def test_delete_not_found(self, mock_get, client):
        mock_engine = MagicMock()
        mock_engine.delete = AsyncMock(return_value=False)
        mock_get.return_value = mock_engine

        resp = client.delete("/memory-engine/project/projects/42/entries/999")
        assert resp.status_code == 404


# ── Search & Versions Tests ─────────────────────────────────────────────────


class TestMemoryEngineRouterSearch:
    """Test search, versions, similarity, and summary endpoints."""

    @patch("memory.routers.memory_engine.get_engine")
    def test_search_entries(self, mock_get, client):
        mock_entry = MagicMock()
        for k, v in _mock_response().items():
            setattr(mock_entry, k, v)
        mock_entry.model_dump = lambda **kw: _mock_response()

        mock_engine = MagicMock()
        mock_engine.search = AsyncMock(return_value=[mock_entry])
        mock_get.return_value = mock_engine

        resp = client.post(
            "/memory-engine/security/projects/42/search",
            json={"query": "authentication"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["domain"] == "security"
        assert data["total"] >= 1

    @patch("memory.routers.memory_engine.get_engine")
    def test_get_versions(self, mock_get, client):
        now = datetime.now(timezone.utc).isoformat()
        mock_version = MagicMock()
        mock_version.id = 1
        mock_version.entry_id = 1
        mock_version.project_id = 42
        mock_version.category = "project"
        mock_version.content = "v1"
        mock_version.metadata_json = {}
        mock_version.version = 1
        mock_version.change_reason = "init"
        mock_version.changed_by = "system"
        mock_version.created_at = now
        mock_version.model_dump = lambda **kw: {
            "id": 1, "entry_id": 1, "project_id": 42,
            "category": "project", "content": "v1",
            "metadata_json": {}, "version": 1,
            "change_reason": "init", "changed_by": "system",
            "created_at": now,
        }

        mock_engine = MagicMock()
        mock_engine.get_versions = AsyncMock(return_value=[mock_version])
        mock_get.return_value = mock_engine

        resp = client.get(
            "/memory-engine/project/projects/42/entries/1/versions",
        )
        assert resp.status_code == 200

    @patch("memory.routers.memory_engine.get_engine")
    def test_similarity_search(self, mock_get, client):
        mock_engine = MagicMock()
        mock_engine.find_similar = AsyncMock(return_value=[
            {"content": "Similar content", "score": 0.95},
        ])
        mock_get.return_value = mock_engine

        resp = client.post(
            "/memory-engine/backend/projects/42/similar",
            json={"query": "authentication", "limit": 5},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["domain"] == "backend"

    @patch("memory.routers.memory_engine.get_engine")
    def test_get_summary(self, mock_get, client):
        mock_engine = MagicMock()
        mock_engine.count = AsyncMock(return_value=10)
        mock_get.return_value = mock_engine

        resp = client.get("/memory-engine/testing/projects/42/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_entries"] == 10
        assert data["domain"] == "testing"


# ── Validation Tests ────────────────────────────────────────────────────────


class TestMemoryEngineRouterValidation:
    """Test request validation."""

    @patch("memory.routers.memory_engine.get_engine")
    def test_create_empty_content_rejected(self, mock_get, client):
        mock_get.return_value = MagicMock()
        resp = client.post(
            "/memory-engine/project/projects/42/entries",
            json={"content": ""},
        )
        assert resp.status_code == 422

    @patch("memory.routers.memory_engine.get_engine")
    def test_search_empty_query_rejected(self, mock_get, client):
        mock_get.return_value = MagicMock()
        resp = client.post(
            "/memory-engine/project/projects/42/search",
            json={"query": ""},
        )
        assert resp.status_code == 422
