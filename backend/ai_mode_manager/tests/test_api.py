"""
API Tests — Phase 5.6
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ai_mode_manager.api.ai_mode_router import router as ai_mode_router


@pytest.fixture
def client():
    from app.core.security import get_current_user
    app = FastAPI()
    app.include_router(ai_mode_router)
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "email": "test@test.com"}
    return TestClient(app)


def test_get_current_mode_endpoint(client):
    resp = client.get("/ai-mode/current")
    assert resp.status_code == 200
    data = resp.json()
    assert "mode" in data
    assert "active_provider" in data


def test_get_providers_endpoint(client):
    resp = client.get("/ai-mode/providers")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2


def test_switch_mode_endpoint(client):
    resp = client.post("/ai-mode/switch", json={"mode": "local"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "local"
