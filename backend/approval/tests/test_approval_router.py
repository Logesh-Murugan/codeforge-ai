"""
Tests for Phase 5.3 — Approval Router (API Tests)

Tests all approval API endpoints using FastAPI TestClient with mocked service.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from approval.router import router as approval_router
from approval.schemas import (
    ApprovalConfigResponse,
    ApprovalDecisionResponse,
    ApprovalHistoryItem,
    PendingApprovalItem,
)


# ── Fixture with auth override ───────────────────────────────────────────────

def _fake_user():
    return {"id": 1, "email": "test@test.com"}


@pytest.fixture
def client():
    from app.core.security import get_current_user

    app = FastAPI()
    app.include_router(approval_router)
    app.dependency_overrides[get_current_user] = lambda: _fake_user()
    return TestClient(app)


# ── Mock Response Builders ───────────────────────────────────────────────────

def _mock_decision_response(decision: str = "approve", status: str = "approved"):
    return ApprovalDecisionResponse(
        project_id=42,
        decision=decision,
        agent_name="solution_architect",
        status=status,
        message=f"Step 'solution_architect' {status}.",
        next_agent="database_engineer",
        updated_at=datetime.now(timezone.utc),
    )


def _mock_pending_item():
    return PendingApprovalItem(
        project_id=42,
        agent_name="solution_architect",
        agent_run_id=101,
        status="pending",
        output={"architecture": "Microservices"},
        next_agent="database_engineer",
        created_at=datetime.now(timezone.utc),
    )


def _mock_history():
    return [
        ApprovalHistoryItem(
            project_id=42,
            agent_name="solution_architect",
            decision="approve",
            feedback="Great work",
            timestamp=datetime.now(timezone.utc),
        )
    ]


def _mock_config_response(approval_mode: bool = True):
    return ApprovalConfigResponse(
        project_id=42,
        approval_mode=approval_mode,
        message="Approval mode updated.",
    )


# ── Router Tests ─────────────────────────────────────────────────────────────

class TestApprovalRouter:

    def test_submit_approve_decision_success(self, client):
        """POST /approval/decide with 'approve' returns 200."""
        with patch(
            "approval.router.ApprovalWorkflowService.process_decision",
            new=AsyncMock(return_value=_mock_decision_response("approve", "approved")),
        ):
            resp = client.post(
                "/approval/decide",
                json={
                    "project_id": 42,
                    "decision": "approve",
                    "agent_name": "solution_architect",
                    "feedback": "Approved",
                },
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["decision"] == "approve"
        assert data["status"] == "approved"

    def test_submit_reject_decision_success(self, client):
        """POST /approval/decide with 'reject' returns 200."""
        with patch(
            "approval.router.ApprovalWorkflowService.process_decision",
            new=AsyncMock(return_value=_mock_decision_response("reject", "rejected")),
        ):
            resp = client.post(
                "/approval/decide",
                json={
                    "project_id": 42,
                    "decision": "reject",
                    "agent_name": "solution_architect",
                    "feedback": "Needs changes",
                },
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["decision"] == "reject"
        assert data["status"] == "rejected"

    def test_submit_regenerate_decision_success(self, client):
        """POST /approval/decide with 'regenerate' returns 200."""
        with patch(
            "approval.router.ApprovalWorkflowService.process_decision",
            new=AsyncMock(return_value=_mock_decision_response("regenerate", "regenerating")),
        ):
            resp = client.post(
                "/approval/decide",
                json={
                    "project_id": 42,
                    "decision": "regenerate",
                    "agent_name": "solution_architect",
                },
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["decision"] == "regenerate"

    def test_submit_edit_decision_success(self, client):
        """POST /approval/decide with 'edit' returns 200."""
        with patch(
            "approval.router.ApprovalWorkflowService.process_decision",
            new=AsyncMock(return_value=_mock_decision_response("edit", "edited")),
        ):
            resp = client.post(
                "/approval/decide",
                json={
                    "project_id": 42,
                    "decision": "edit",
                    "agent_name": "solution_architect",
                    "edited_output": {"architecture": "Monolith"},
                },
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["decision"] == "edit"

    def test_submit_continue_decision_success(self, client):
        """POST /approval/decide with 'continue' returns 200."""
        with patch(
            "approval.router.ApprovalWorkflowService.process_decision",
            new=AsyncMock(return_value=_mock_decision_response("continue", "running")),
        ):
            resp = client.post(
                "/approval/decide",
                json={
                    "project_id": 42,
                    "decision": "continue",
                },
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["decision"] == "continue"

    def test_submit_decision_bad_request(self, client):
        """ValueError from service returns 400."""
        with patch(
            "approval.router.ApprovalWorkflowService.process_decision",
            new=AsyncMock(side_effect=ValueError("Invalid decision payload")),
        ):
            resp = client.post(
                "/approval/decide",
                json={
                    "project_id": 42,
                    "decision": "edit",
                },
            )
        assert resp.status_code == 400

    def test_get_pending_approval_success(self, client):
        """GET /approval/pending/{project_id} returns 200."""
        with patch(
            "approval.router.ApprovalWorkflowService.get_pending_approval",
            new=AsyncMock(return_value=_mock_pending_item()),
        ):
            resp = client.get("/approval/pending/42")
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == 42
        assert data["agent_name"] == "solution_architect"

    def test_get_pending_approval_404(self, client):
        """GET /approval/pending/{project_id} when none returns 404."""
        with patch(
            "approval.router.ApprovalWorkflowService.get_pending_approval",
            new=AsyncMock(return_value=None),
        ):
            resp = client.get("/approval/pending/42")
        assert resp.status_code == 404

    def test_get_approval_history_success(self, client):
        """GET /approval/history/{project_id} returns 200 with list."""
        with patch(
            "approval.router.ApprovalWorkflowService.get_approval_history",
            new=AsyncMock(return_value=_mock_history()),
        ):
            resp = client.get("/approval/history/42")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["decision"] == "approve"

    def test_set_approval_config_success(self, client):
        """POST /approval/config returns 200."""
        with patch(
            "approval.router.ApprovalWorkflowService.set_approval_config",
            new=AsyncMock(return_value=_mock_config_response(True)),
        ):
            resp = client.post(
                "/approval/config",
                json={
                    "project_id": 42,
                    "approval_mode": True,
                },
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["approval_mode"] is True
