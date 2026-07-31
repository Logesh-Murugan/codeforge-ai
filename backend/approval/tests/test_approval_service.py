"""
Tests for Phase 5.3 — ApprovalWorkflowService (Unit Tests)

Tests Approve, Reject, Regenerate, Edit, Continue, and Config management.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from approval.schemas import (
    ApprovalDecisionRequest,
    DecisionType,
)
from approval.service import ApprovalWorkflowService


# ── Fixtures & Mock Helpers ──────────────────────────────────────────────────

def _mock_pipeline_state(
    pending: bool = True,
    agent_name: str = "solution_architect",
    next_agent: str = "database_engineer",
):
    state = {
        "project_id": 42,
        "project_idea": "Build a SaaS app",
        "current_agent": agent_name,
        "approval_mode": True,
        "approval_status": "pending" if pending else "approved",
        "pending_approval": {
            "agent_name": agent_name,
            "agent_run_id": 101,
            "project_id": 42,
            "next_agent": next_agent,
            "output": {"architecture": "Microservices"},
        } if pending else None,
        "approval_history": [],
    }
    return state


# ── ApprovalWorkflowService Tests ─────────────────────────────────────────────

class TestApprovalWorkflowService:

    @pytest.mark.asyncio
    async def test_get_pending_approval_found(self):
        """get_pending_approval returns item when state has pending approval."""
        mock_state = _mock_pipeline_state(pending=True)
        with patch("approval.service.get_pipeline_state", return_value=mock_state):
            service = ApprovalWorkflowService()
            pending = await service.get_pending_approval(42)

        assert pending is not None
        assert pending.project_id == 42
        assert pending.agent_name == "solution_architect"
        assert pending.next_agent == "database_engineer"
        assert pending.status == "pending"

    @pytest.mark.asyncio
    async def test_get_pending_approval_none_when_not_pending(self):
        """get_pending_approval returns None when no pending item."""
        mock_state = _mock_pipeline_state(pending=False)
        with patch("approval.service.get_pipeline_state", return_value=mock_state):
            service = ApprovalWorkflowService()
            pending = await service.get_pending_approval(42)

        assert pending is None

    @pytest.mark.asyncio
    async def test_approve_decision(self):
        """Approve decision sets approved status and resumes pipeline."""
        mock_state = _mock_pipeline_state(pending=True)
        req = ApprovalDecisionRequest(
            project_id=42,
            decision=DecisionType.APPROVE,
            feedback="Looks good",
        )

        with patch("approval.service.get_pipeline_state", return_value=mock_state), \
             patch("approval.service.update_agent_run", new=AsyncMock()) as mock_update_db, \
             patch("approval.service.update_graph_state") as mock_update_graph, \
             patch("approval.service.resume_pipeline", new=AsyncMock()) as mock_resume:

            service = ApprovalWorkflowService()
            res = await service.process_decision(req)

            assert res.decision == "approve"
            assert res.status == "approved"
            assert res.next_agent == "database_engineer"
            mock_update_db.assert_called_once_with(101, "completed")
            mock_update_graph.assert_called_once()
            mock_resume.assert_called_once_with(42)

    @pytest.mark.asyncio
    async def test_reject_decision(self):
        """Reject decision sets rejected status and halts execution."""
        mock_state = _mock_pipeline_state(pending=True)
        req = ApprovalDecisionRequest(
            project_id=42,
            decision=DecisionType.REJECT,
            feedback="Incorrect architecture",
        )

        with patch("approval.service.get_pipeline_state", return_value=mock_state), \
             patch("approval.service.update_agent_run", new=AsyncMock()) as mock_update_db, \
             patch("approval.service.update_graph_state") as mock_update_graph:

            service = ApprovalWorkflowService()
            res = await service.process_decision(req)

            assert res.decision == "reject"
            assert res.status == "rejected"
            mock_update_db.assert_called_once_with(101, "rejected", error_message="Incorrect architecture")
            mock_update_graph.assert_called_once()

    @pytest.mark.asyncio
    async def test_regenerate_decision(self):
        """Regenerate decision sets regenerating status and re-runs node."""
        mock_state = _mock_pipeline_state(pending=True)
        req = ApprovalDecisionRequest(
            project_id=42,
            decision=DecisionType.REGENERATE,
            feedback="Re-try with Postgres",
        )

        with patch("approval.service.get_pipeline_state", return_value=mock_state), \
             patch("approval.service.update_agent_run", new=AsyncMock()) as mock_update_db, \
             patch("approval.service.update_graph_state") as mock_update_graph, \
             patch("approval.service.resume_pipeline", new=AsyncMock()) as mock_resume:

            service = ApprovalWorkflowService()
            res = await service.process_decision(req)

            assert res.decision == "regenerate"
            assert res.status == "regenerating"
            mock_update_db.assert_called_once_with(101, "regenerating")
            mock_update_graph.assert_called_once()
            mock_resume.assert_called_once_with(42)

    @pytest.mark.asyncio
    async def test_edit_decision_success(self):
        """Edit decision overrides output and approves step."""
        mock_state = _mock_pipeline_state(pending=True)
        edited_json = {"architecture": "Monolith", "db": "PostgreSQL"}
        req = ApprovalDecisionRequest(
            project_id=42,
            decision=DecisionType.EDIT,
            agent_name="solution_architect",
            edited_output=edited_json,
            feedback="Manually changed to monolith",
        )

        with patch("approval.service.get_pipeline_state", return_value=mock_state), \
             patch("approval.service.update_agent_run", new=AsyncMock()) as mock_update_db, \
             patch("approval.service.update_graph_state") as mock_update_graph, \
             patch("approval.service.resume_pipeline", new=AsyncMock()) as mock_resume:

            service = ApprovalWorkflowService()
            res = await service.process_decision(req)

            assert res.decision == "edit"
            assert res.status == "edited"
            mock_update_db.assert_called_once_with(101, "completed", output_json=edited_json)
            mock_update_graph.assert_called_once()
            mock_resume.assert_called_once_with(42)

    @pytest.mark.asyncio
    async def test_edit_decision_requires_edited_output(self):
        """Edit decision without edited_output raises ValueError."""
        mock_state = _mock_pipeline_state(pending=True)
        req = ApprovalDecisionRequest(
            project_id=42,
            decision=DecisionType.EDIT,
            edited_output=None,
        )

        with patch("approval.service.get_pipeline_state", return_value=mock_state):
            service = ApprovalWorkflowService()
            with pytest.raises(ValueError, match="edited_output is required"):
                await service.process_decision(req)

    @pytest.mark.asyncio
    async def test_continue_decision(self):
        """Continue decision resumes pipeline execution."""
        mock_state = _mock_pipeline_state(pending=False)
        req = ApprovalDecisionRequest(
            project_id=42,
            decision=DecisionType.CONTINUE,
        )

        with patch("approval.service.get_pipeline_state", return_value=mock_state), \
             patch("approval.service.update_graph_state") as mock_update_graph, \
             patch("approval.service.resume_pipeline", new=AsyncMock()) as mock_resume:

            service = ApprovalWorkflowService()
            res = await service.process_decision(req)

            assert res.decision == "continue"
            assert res.status == "running"
            mock_resume.assert_called_once_with(42)

    @pytest.mark.asyncio
    async def test_set_approval_config(self):
        """set_approval_config updates approval mode setting."""
        mock_state = _mock_pipeline_state(pending=False)
        with patch("approval.service.get_pipeline_state", return_value=mock_state), \
             patch("approval.service.update_graph_state") as mock_update_graph:

            service = ApprovalWorkflowService()
            res = await service.set_approval_config(42, approval_mode=True)

            assert res.project_id == 42
            assert res.approval_mode is True
            mock_update_graph.assert_called_once_with(42, {"approval_mode": True})
