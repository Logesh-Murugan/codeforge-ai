"""
API Tests — Phase 5.8
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from validation_pipeline.api.validation_router import router as validation_router


@pytest.fixture
def client():
    from app.core.security import get_current_user
    app = FastAPI()
    app.include_router(validation_router)
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "email": "test@test.com"}
    return TestClient(app)


def test_get_status_endpoint(client):
    resp = client.get("/validation/status?project_id=1")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "overall_score" in data


def test_get_latest_endpoint(client):
    resp = client.get("/validation/latest?project_id=1")
    assert resp.status_code == 200
    data = resp.json()
    assert "stage_results" in data


def test_post_run_endpoint(client):
    resp = client.post("/validation/run", json={"project_id": 1})
    assert resp.status_code == 200
    data = resp.json()
    assert "overall_score" in data
