"""
Integration Tests — Phase 5.4

Integration tests for collaboration routes and context exchange.
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from collaboration.routers.collaboration import router as collaboration_router
from collaboration.schemas.communication import ContextBundleResponse


@pytest.fixture
def client():
    from app.core.security import get_current_user
    app = FastAPI()
    app.include_router(collaboration_router)
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "email": "test@test.com"}
    return TestClient(app)


def test_get_collaboration_status_endpoint(client):
    resp = client.get("/collaboration/status/42")
    assert resp.status_code == 200
    data = resp.json()
    assert data["project_id"] == 42
    assert "active_collaborators" in data


def test_get_relationships_endpoint(client):
    resp = client.get("/collaboration/relationships/42")
    assert resp.status_code == 200
    data = resp.json()
    assert data["project_id"] == 42
    assert len(data["agents"]) == 13


def test_get_context_bundle_endpoint(client):
    mock_bundle = ContextBundleResponse(
        project_id=42,
        target_agent="backend_developer",
        requirements={"summary": "E-commerce App"},
        architecture={"style": "Microservices"},
    )
    with patch("collaboration.routers.collaboration.CollaborationEngineService.get_context_bundle", new=AsyncMock(return_value=mock_bundle)):
        resp = client.get("/collaboration/context/42/backend_developer")
    assert resp.status_code == 200
    data = resp.json()
    assert data["target_agent"] == "backend_developer"
    assert data["requirements"] is not None
