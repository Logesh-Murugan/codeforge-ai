"""
API Tests — Phase 5.10
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from portfolio.api.portfolio_router import router as portfolio_router


@pytest.fixture
def client():
    from app.core.security import get_current_user
    app = FastAPI()
    app.include_router(portfolio_router)
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "email": "test@test.com"}
    return TestClient(app)


def test_get_portfolio_endpoint(client):
    resp = client.get("/portfolio/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["project_id"] == 1
    assert "metrics" in data


def test_get_metrics_endpoint(client):
    resp = client.get("/portfolio/metrics/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["lines_of_code"] > 0


def test_get_reports_endpoint(client):
    resp = client.get("/portfolio/reports/1?format=md")
    assert resp.status_code == 200
    data = resp.json()
    assert "content" in data


def test_get_architecture_endpoint(client):
    resp = client.get("/portfolio/architecture/1")
    assert resp.status_code == 200
    data = resp.json()
    assert "system_architecture" in data
