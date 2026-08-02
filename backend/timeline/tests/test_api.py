"""
API Tests — Phase 5.9
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from timeline.api.timeline_router import router as timeline_router


@pytest.fixture
def client():
    from app.core.security import get_current_user
    app = FastAPI()
    app.include_router(timeline_router)
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "email": "test@test.com"}
    return TestClient(app)


def test_get_timeline_endpoint(client):
    resp = client.get("/timeline/1")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_milestones_endpoint(client):
    resp = client.get("/timeline/milestones/1")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 9


def test_get_statistics_endpoint(client):
    resp = client.get("/timeline/statistics/1")
    assert resp.status_code == 200
    data = resp.json()
    assert "overall_progress_pct" in data


def test_get_analytics_endpoint(client):
    resp = client.get("/timeline/analytics/1")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_events" in data
