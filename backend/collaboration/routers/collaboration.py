"""
Collaboration Router — Phase 5.4

FastAPI route handlers for Agent Collaboration Engine.

Endpoints:
    GET  /collaboration/status/{project_id}       Active collaborators status & progress
    POST /collaboration/message                   Record inter-agent message
    GET  /collaboration/context/{project_id}/{agent_name} Context bundle for an agent
    GET  /collaboration/history/{project_id}      Execution trace & log history
    GET  /collaboration/reports/{project_id}      Collaboration report & metrics
    POST /collaboration/reports/{project_id}      Generate/re-calculate report
    GET  /collaboration/relationships/{project_id} Agent dependency matrix & map
    PUT  /collaboration/relationships/{project_id} Update relationship weights
    GET  /collaboration/feedback/{project_id}     Feedback history
    POST /collaboration/feedback                  Submit feedback
    PUT  /collaboration/feedback/{feedback_id}    Update feedback status
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from collaboration.schemas import (
    AgentMessageRequest,
    AgentMessageResponse,
    CollaborationReportResponse,
    CollaborationStatusResponse,
    ContextBundleResponse,
    CrossValidationRequest,
    CrossValidationResponse,
    FeedbackRequest,
    FeedbackResponse,
    RelationshipMapResponse,
    UpdateFeedbackRequest,
)
from collaboration.services.analytics_service import AnalyticsService
from collaboration.services.collaboration_service import CollaborationEngineService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/collaboration", tags=["collaboration"])


def _collaboration_service() -> CollaborationEngineService:
    return CollaborationEngineService()


def _analytics_service() -> AnalyticsService:
    return AnalyticsService()


# ── Status Endpoints ──────────────────────────────────────────────────────────

@router.get(
    "/status/{project_id}",
    response_model=CollaborationStatusResponse,
    summary="Get active collaborators status and progress",
)
async def get_collaboration_status(
    project_id: int,
    _user=Depends(get_current_user),
    analytics: AnalyticsService = Depends(_analytics_service),
):
    """
    Return real-time status of all 13 collaborating agents for a project.
    """
    try:
        return await analytics.get_collaboration_status(project_id)
    except Exception as exc:
        logger.error(f"[COLLABORATION-ROUTER] get_collaboration_status failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


@router.post(
    "/status/{project_id}",
    response_model=CollaborationStatusResponse,
    summary="Refresh or initialize collaboration status",
)
async def refresh_collaboration_status(
    project_id: int,
    _user=Depends(get_current_user),
    analytics: AnalyticsService = Depends(_analytics_service),
):
    """
    POST route to refresh or initialize collaboration status.
    """
    return await analytics.get_collaboration_status(project_id)


# ── History & Tracing Endpoints ───────────────────────────────────────────────

@router.get(
    "/history/{project_id}",
    response_model=List[Dict[str, Any]],
    summary="Get collaboration history and execution trace",
)
async def get_collaboration_history(
    project_id: int,
    _user=Depends(get_current_user),
    service: CollaborationEngineService = Depends(_collaboration_service),
):
    """
    Retrieve full execution trace and log history of inter-agent messages.
    """
    return await service.get_collaboration_history(project_id)


@router.post(
    "/message",
    response_model=AgentMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record inter-agent message or context transfer",
)
async def send_agent_message(
    body: AgentMessageRequest,
    _user=Depends(get_current_user),
    service: CollaborationEngineService = Depends(_collaboration_service),
):
    """
    Record an inter-agent message or context transfer.
    """
    try:
        return await service.send_message(body)
    except Exception as exc:
        logger.error(f"[COLLABORATION-ROUTER] send_agent_message failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


@router.get(
    "/context/{project_id}/{agent_name}",
    response_model=ContextBundleResponse,
    summary="Get multi-agent context bundle for an agent",
)
async def get_agent_context(
    project_id: int,
    agent_name: str,
    _user=Depends(get_current_user),
    service: CollaborationEngineService = Depends(_collaboration_service),
):
    """
    Assemble and return the multi-agent context bundle required by `agent_name`.
    """
    return await service.get_context_bundle(project_id, agent_name)


# ── Reports Endpoints ─────────────────────────────────────────────────────────

@router.get(
    "/reports/{project_id}",
    response_model=CollaborationReportResponse,
    summary="Get collaboration report and scores",
)
async def get_collaboration_report(
    project_id: int,
    _user=Depends(get_current_user),
    analytics: AnalyticsService = Depends(_analytics_service),
):
    """
    Get detailed collaboration report including overall score, consensus rating, information density, and friction score.
    """
    return await analytics.get_collaboration_report(project_id)


@router.post(
    "/reports/{project_id}",
    response_model=CollaborationReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate/re-calculate collaboration report",
)
async def generate_collaboration_report(
    project_id: int,
    _user=Depends(get_current_user),
    analytics: AnalyticsService = Depends(_analytics_service),
):
    """
    Generate or re-calculate collaboration report for a project.
    """
    return await analytics.get_collaboration_report(project_id)


# ── Relationships Endpoints ───────────────────────────────────────────────────

@router.get(
    "/relationships/{project_id}",
    response_model=RelationshipMapResponse,
    summary="Get agent dependency matrix and relationship map",
)
async def get_relationships(
    project_id: int,
    _user=Depends(get_current_user),
    analytics: AnalyticsService = Depends(_analytics_service),
):
    """
    Return dependency matrix and relationship network between all 13 agents.
    """
    return await analytics.get_relationship_map(project_id)


@router.put(
    "/relationships/{project_id}",
    response_model=RelationshipMapResponse,
    summary="Update relationship weights or matrix",
)
async def update_relationships(
    project_id: int,
    _user=Depends(get_current_user),
    analytics: AnalyticsService = Depends(_analytics_service),
):
    """
    PUT endpoint to update or recalculate agent relationship matrix.
    """
    return await analytics.get_relationship_map(project_id)


# ── Feedback Endpoints ────────────────────────────────────────────────────────

@router.get(
    "/feedback/{project_id}",
    response_model=List[FeedbackResponse],
    summary="Get feedback history for a project",
)
async def get_feedback_history(
    project_id: int,
    _user=Depends(get_current_user),
    service: CollaborationEngineService = Depends(_collaboration_service),
):
    """
    Fetch all cross-agent feedback entries for a project.
    """
    return await service.get_feedback_history(project_id)


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit cross-agent feedback",
)
async def submit_feedback(
    body: FeedbackRequest,
    _user=Depends(get_current_user),
    service: CollaborationEngineService = Depends(_collaboration_service),
):
    """
    Submit cross-agent feedback.
    """
    try:
        return await service.submit_feedback(body)
    except Exception as exc:
        logger.error(f"[COLLABORATION-ROUTER] submit_feedback failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


@router.put(
    "/feedback/{feedback_id}",
    response_model=FeedbackResponse,
    summary="Update feedback resolution status",
)
async def update_feedback_status(
    feedback_id: int,
    body: UpdateFeedbackRequest,
    _user=Depends(get_current_user),
    service: CollaborationEngineService = Depends(_collaboration_service),
):
    """
    Update status of a feedback entry (open -> resolved/ignored).
    """
    try:
        return await service.update_feedback_status(feedback_id, body)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except Exception as exc:
        logger.error(f"[COLLABORATION-ROUTER] update_feedback_status failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


# ── Cross-Validation Endpoint ─────────────────────────────────────────────────

@router.post(
    "/validate",
    response_model=CrossValidationResponse,
    summary="Run cross-agent validation check",
)
async def validate_cross_agent(
    body: CrossValidationRequest,
    _user=Depends(get_current_user),
    service: CollaborationEngineService = Depends(_collaboration_service),
):
    """
    Conduct cross-agent validation between a validator agent and target agent.
    """
    try:
        return await service.validate_cross_agent(body)
    except Exception as exc:
        logger.error(f"[COLLABORATION-ROUTER] validate_cross_agent failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )
