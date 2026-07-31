"""
Context API Tests — Phase 5.5
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from context_engine.routers.context_router import router as context_router
from context_engine.schemas.context_payload import ContextEntityResponse


@pytest.fixture
def client():
    from app.core.security import get_current_user
    app = FastAPI()
    app.include_router(context_router)
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "email": "test@test.com"}
    return TestClient(app)


def test_get_context_bundle_endpoint(client):
    with patch(
        "context_engine.services.context_retrieval_service.ContextRetrievalService.retrieve_context_bundle",
        new=AsyncMock(return_value={"Project": {"id": 42}}),
    ):
        resp = client.get("/context/bundle/42/backend_developer")
    assert resp.status_code == 200
    data = resp.json()
    assert "Project" in data


def test_get_context_scores_endpoint(client):
    resp = client.get("/context/scores/42")
    assert resp.status_code == 200
    data = resp.json()
    assert "overall_quality_score" in data


def test_get_context_visualization_endpoint(client):
    resp = client.get("/context/visualization/42")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["nodes"]) == 21
