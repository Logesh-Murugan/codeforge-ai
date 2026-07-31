"""
Approval Router — Phase 5.3

FastAPI route handlers for Human Approval Workflow System.

Endpoints:
    POST /approval/decide               Submit human approval decision
    GET  /approval/pending/{project_id} Fetch current pending approval item
    GET  /approval/history/{project_id} Fetch approval history log
    POST /approval/config               Configure approval mode per project
"""
from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from approval.schemas import (
    ApprovalConfigRequest,
    ApprovalConfigResponse,
    ApprovalDecisionRequest,
    ApprovalDecisionResponse,
    ApprovalHistoryItem,
    PendingApprovalItem,
)
from approval.service import ApprovalWorkflowService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/approval", tags=["approval"])


def _approval_service() -> ApprovalWorkflowService:
    return ApprovalWorkflowService()


@router.post(
    "/decide",
    response_model=ApprovalDecisionResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit a human decision for a pipeline step (Approve, Reject, Regenerate, Edit, Continue)",
)
async def submit_decision(
    body: ApprovalDecisionRequest,
    _user=Depends(get_current_user),
    service: ApprovalWorkflowService = Depends(_approval_service),
):
    """
    Submit a human decision for a pipeline step waiting for approval.

    - **approve**: Accept current step output and advance pipeline.
    - **reject**: Reject output and halt execution.
    - **regenerate**: Re-run current agent node for fresh output.
    - **edit**: Override output JSON with edited payload and advance.
    - **continue**: Resume execution from paused checkpoint state.
    """
    try:
        return await service.process_decision(body)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    except Exception as exc:
        logger.error(f"[APPROVAL-ROUTER] submit_decision failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


@router.get(
    "/pending/{project_id}",
    response_model=PendingApprovalItem,
    summary="Get pending approval details for a project",
)
async def get_pending_approval(
    project_id: int,
    _user=Depends(get_current_user),
    service: ApprovalWorkflowService = Depends(_approval_service),
):
    """
    Retrieve the current step output waiting for human approval.
    Returns 404 if no item is currently pending approval.
    """
    item = await service.get_pending_approval(project_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No pending approval item for project {project_id}.",
        )
    return item


@router.get(
    "/history/{project_id}",
    response_model=List[ApprovalHistoryItem],
    summary="Get approval audit history for a project",
)
async def get_approval_history(
    project_id: int,
    _user=Depends(get_current_user),
    service: ApprovalWorkflowService = Depends(_approval_service),
):
    """
    Return all past approval decisions logged for a project.
    """
    return await service.get_approval_history(project_id)


@router.post(
    "/config",
    response_model=ApprovalConfigResponse,
    summary="Enable or disable human approval mode for a project",
)
async def set_approval_config(
    body: ApprovalConfigRequest,
    _user=Depends(get_current_user),
    service: ApprovalWorkflowService = Depends(_approval_service),
):
    """
    Toggle whether human approval is required between agent steps.
    """
    return await service.set_approval_config(body.project_id, body.approval_mode)
