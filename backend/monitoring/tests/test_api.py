"""
API Tests — Phase 5.7
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from monitoring.api.monitoring_router import router as monitoring_router


@pytest.fixture
def client():
    from app.core.security import get_current_user
    app = FastAPI()
    app.include_router(monitoring_router)
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "email": "test@test.com"}
    return TestClient(app)


def test_get_status_endpoint(client):
    resp = client.get("/monitoring/status?project_id=1")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert len(data["agents"]) == 13


def test_get_metrics_endpoint(client):
    resp = client.get("/monitoring/metrics?project_id=1")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_execution_time_ms" in data


def test_get_dashboard_endpoint(client):
    resp = client.get("/monitoring/dashboard?project_id=1")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "metrics" in data
    assert "timeline" in data
    assert "logs" in data
