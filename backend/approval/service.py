"""
ApprovalWorkflowService — Phase 5.3

Business logic for the Human Approval Workflow System.
Supports Approve, Reject, Regenerate, Edit, and Continue.
Interacts safely with LangGraph state checkpointer and SQL database.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from approval.schemas import (
    ApprovalConfigResponse,
    ApprovalDecisionRequest,
    ApprovalDecisionResponse,
    ApprovalHistoryItem,
    DecisionType,
    PendingApprovalItem,
)
from orchestrator.graph import get_pipeline_state, resume_pipeline, update_graph_state
from orchestrator.nodes import update_agent_run

logger = logging.getLogger(__name__)


class ApprovalWorkflowService:
    """
    Service managing human-in-the-loop decisions and state transitions.
    """

    async def get_pending_approval(self, project_id: int) -> Optional[PendingApprovalItem]:
        """
        Fetch the current pending approval request for a project.
        """
        state = get_pipeline_state(project_id)
        if not state:
            return None

        pending = state.get("pending_approval")
        if not pending or state.get("approval_status") != "pending":
            return None

        return PendingApprovalItem(
            project_id=project_id,
            agent_name=pending.get("agent_name", "unknown"),
            agent_run_id=pending.get("agent_run_id"),
            status="pending",
            output=pending.get("output"),
            next_agent=pending.get("next_agent"),
        )

    async def get_approval_history(self, project_id: int) -> List[ApprovalHistoryItem]:
        """
        Fetch the audit trail of approval decisions for a project.
        """
        state = get_pipeline_state(project_id)
        if not state:
            return []

        history = state.get("approval_history") or []
        items: List[ApprovalHistoryItem] = []
        for entry in history:
            try:
                items.append(
                    ApprovalHistoryItem(
                        project_id=project_id,
                        agent_name=entry.get("agent_name", "unknown"),
                        decision=entry.get("decision", "unknown"),
                        feedback=entry.get("feedback"),
                        timestamp=entry.get("timestamp", datetime.now(timezone.utc)),
                    )
                )
            except Exception as exc:
                logger.warning(f"[APPROVAL] Error parsing history entry: {exc}")
        return items

    async def process_decision(
        self, request: ApprovalDecisionRequest
    ) -> ApprovalDecisionResponse:
        """
        Process a human approval decision (Approve, Reject, Regenerate, Edit, Continue).
        """
        project_id = request.project_id
        decision = request.decision

        logger.info(
            f"[APPROVAL] Processing decision '{decision.value}' for project {project_id}"
        )

        state = get_pipeline_state(project_id)
        if not state:
            raise ValueError(f"No active pipeline state found for project {project_id}")

        pending = state.get("pending_approval") or {}
        agent_name = request.agent_name or pending.get("agent_name") or state.get("current_agent") or "unknown"
        agent_run_id = pending.get("agent_run_id")

        if decision == DecisionType.APPROVE:
            return await self._handle_approve(project_id, agent_name, agent_run_id, request.feedback)
        elif decision == DecisionType.REJECT:
            return await self._handle_reject(project_id, agent_name, agent_run_id, request.feedback)
        elif decision == DecisionType.REGENERATE:
            return await self._handle_regenerate(project_id, agent_name, agent_run_id, request.feedback)
        elif decision == DecisionType.EDIT:
            if not request.edited_output:
                raise ValueError("edited_output is required when decision is 'edit'")
            return await self._handle_edit(
                project_id, agent_name, agent_run_id, request.edited_output, request.feedback
            )
        elif decision == DecisionType.CONTINUE:
            return await self._handle_continue(project_id, agent_name, request.feedback)
        else:
            raise ValueError(f"Unsupported decision type: {decision}")

    async def _handle_approve(
        self, project_id: int, agent_name: str, agent_run_id: Optional[int], feedback: Optional[str]
    ) -> ApprovalDecisionResponse:
        """Approve the pending step and resume graph execution."""
        state = get_pipeline_state(project_id) or {}
        pending = state.get("pending_approval") or {}
        next_agent = pending.get("next_agent")

        # Record history
        history = list(state.get("approval_history") or [])
        history.append({
            "agent_name": agent_name,
            "decision": "approve",
            "feedback": feedback,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # Update DB if agent_run_id exists
        if agent_run_id:
            await update_agent_run(agent_run_id, "completed")

        # Update state checkpointer
        state_update = {
            "approval_status": "approved",
            "pending_approval": None,
            "approval_history": history,
            "current_agent": next_agent
        }
        update_graph_state(project_id, state_update)

        # Resume pipeline asynchronously
        try:
            await resume_pipeline(project_id)
        except Exception as exc:
            logger.warning(f"[APPROVAL] Resume pipeline notice: {exc}")

        return ApprovalDecisionResponse(
            project_id=project_id,
            decision="approve",
            agent_name=agent_name,
            status="approved",
            message=f"Step '{agent_name}' approved. Pipeline resumed.",
            next_agent=next_agent
        )

    async def _handle_reject(
        self, project_id: int, agent_name: str, agent_run_id: Optional[int], feedback: Optional[str]
    ) -> ApprovalDecisionResponse:
        """Reject the pending step and halt pipeline execution."""
        state = get_pipeline_state(project_id) or {}
        history = list(state.get("approval_history") or [])
        history.append({
            "agent_name": agent_name,
            "decision": "reject",
            "feedback": feedback,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        if agent_run_id:
            await update_agent_run(agent_run_id, "rejected", error_message=feedback or "User rejected step")

        state_update = {
            "approval_status": "rejected",
            "pending_approval": None,
            "approval_history": history,
            "error": f"Step '{agent_name}' rejected by human operator."
        }
        update_graph_state(project_id, state_update)

        return ApprovalDecisionResponse(
            project_id=project_id,
            decision="reject",
            agent_name=agent_name,
            status="rejected",
            message=f"Step '{agent_name}' rejected. Pipeline halted.",
            current_agent=agent_name
        )

    async def _handle_regenerate(
        self, project_id: int, agent_name: str, agent_run_id: Optional[int], feedback: Optional[str]
    ) -> ApprovalDecisionResponse:
        """Mark step for regeneration and trigger re-execution."""
        state = get_pipeline_state(project_id) or {}
        history = list(state.get("approval_history") or [])
        history.append({
            "agent_name": agent_name,
            "decision": "regenerate",
            "feedback": feedback,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        if agent_run_id:
            await update_agent_run(agent_run_id, "regenerating")

        # Set state to allow node re-execution
        state_update = {
            "approval_status": "regenerate",
            "pending_approval": None,
            "approval_history": history,
            "current_agent": agent_name,
            agent_name: None  # clear previous agent output to force fresh generation
        }
        update_graph_state(project_id, state_update)

        # Trigger re-execution
        try:
            await resume_pipeline(project_id)
        except Exception as exc:
            logger.warning(f"[APPROVAL] Re-execution notice: {exc}")

        return ApprovalDecisionResponse(
            project_id=project_id,
            decision="regenerate",
            agent_name=agent_name,
            status="regenerating",
            message=f"Step '{agent_name}' queued for regeneration.",
            current_agent=agent_name
        )

    async def _handle_edit(
        self,
        project_id: int,
        agent_name: str,
        agent_run_id: Optional[int],
        edited_output: Dict[str, Any],
        feedback: Optional[str],
    ) -> ApprovalDecisionResponse:
        """Override agent output with human edits and approve step."""
        state = get_pipeline_state(project_id) or {}
        pending = state.get("pending_approval") or {}
        next_agent = pending.get("next_agent")

        history = list(state.get("approval_history") or [])
        history.append({
            "agent_name": agent_name,
            "decision": "edit",
            "feedback": feedback or "Output edited by user",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        if agent_run_id:
            await update_agent_run(agent_run_id, "completed", output_json=edited_output)

        state_update = {
            agent_name: edited_output,  # Update agent output field in state
            "approval_status": "edited",
            "pending_approval": None,
            "approval_history": history,
            "current_agent": next_agent
        }
        update_graph_state(project_id, state_update)

        try:
            await resume_pipeline(project_id)
        except Exception as exc:
            logger.warning(f"[APPROVAL] Resume pipeline notice after edit: {exc}")

        return ApprovalDecisionResponse(
            project_id=project_id,
            decision="edit",
            agent_name=agent_name,
            status="edited",
            message=f"Output for '{agent_name}' updated and approved. Pipeline resumed.",
            next_agent=next_agent
        )

    async def _handle_continue(
        self, project_id: int, agent_name: str, feedback: Optional[str]
    ) -> ApprovalDecisionResponse:
        """Resume pipeline execution from current state."""
        state = get_pipeline_state(project_id) or {}
        current_agent = state.get("current_agent", agent_name)

        history = list(state.get("approval_history") or [])
        history.append({
            "agent_name": current_agent,
            "decision": "continue",
            "feedback": feedback,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        state_update = {
            "approval_status": "continued",
            "pending_approval": None,
            "approval_history": history
        }
        update_graph_state(project_id, state_update)

        await resume_pipeline(project_id)

        return ApprovalDecisionResponse(
            project_id=project_id,
            decision="continue",
            agent_name=current_agent,
            status="running",
            message="Pipeline execution resumed.",
            current_agent=current_agent
        )

    async def set_approval_config(
        self, project_id: int, approval_mode: bool
    ) -> ApprovalConfigResponse:
        """
        Enable or disable human approval mode for a project.
        """
        state_update = {"approval_mode": approval_mode}
        state = get_pipeline_state(project_id)
        if state:
            update_graph_state(project_id, state_update)

        mode_str = "enabled" if approval_mode else "disabled"
        return ApprovalConfigResponse(
            project_id=project_id,
            approval_mode=approval_mode,
            message=f"Human approval mode {mode_str} for project {project_id}.",
        )
