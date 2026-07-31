"""
Context Router — Phase 5.5

FastAPI route handlers for the Context Sharing Engine.

Endpoints:
    GET    /context/bundle/{project_id}/{agent_name} Context bundle for an agent
    POST   /context                                  Register/create a new context entry
    GET    /context/{context_id}                     Retrieve context by ID
    PUT    /context/{context_id}                     Update context payload & bump version
    DELETE /context/{context_id}                     Invalidate/soft-delete context entity
    POST   /context/validate                         Run context validation suite
    GET    /context/scores/{project_id}              Fetch 6-tier quality score metrics
    GET    /context/consumers/{project_id}           List context consumers and audit log
    GET    /context/producers/{project_id}           List context producers
    GET    /context/history/{project_id}             Full context version & change history
    GET    /context/visualization/{project_id}       Context flow graph visualization payload
    GET    /context/reports/{project_id}             Project context audit report
    POST   /context/reports/{project_id}             Generate/re-calculate audit report
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from context_engine.managers.context_history_manager import ContextHistoryManager
from context_engine.managers.context_manager import ContextManager
from context_engine.schemas import (
    ContextCreateRequest,
    ContextEntityResponse,
    ContextHistoryRecord,
    ContextQualityScoreResponse,
    ContextReportResponse,
    ContextValidationResponse,
    ContextVisualizationResponse,
)

from context_engine.services.context_retrieval_service import ContextRetrievalService
from context_engine.services.context_scoring_service import ContextScoringService
from context_engine.validators.context_validator import ContextValidator
from context_engine.visualization.flow_generator import ContextFlowGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/context", tags=["context-engine"])


def _retrieval_service() -> ContextRetrievalService:
    return ContextRetrievalService()


def _manager() -> ContextManager:
    return ContextManager()


def _history_manager() -> ContextHistoryManager:
    return ContextHistoryManager()


def _validator() -> ContextValidator:
    return ContextValidator()


def _scoring_service() -> ContextScoringService:
    return ContextScoringService()


def _flow_generator() -> ContextFlowGenerator:
    return ContextFlowGenerator()


# ── Context Bundle & Entity Endpoints ─────────────────────────────────────────

@router.get(
    "/bundle/{project_id}/{agent_name}",
    response_model=Dict[str, Any],
    summary="Get aggregated & routed context bundle for an agent",
)
async def get_context_bundle(
    project_id: int,
    agent_name: str,
    _user=Depends(get_current_user),
    service: ContextRetrievalService = Depends(_retrieval_service),
):
    """
    Retrieve routed context bundle specific to `agent_name`.
    """
    return await service.retrieve_context_bundle(project_id, agent_name)


@router.post(
    "",
    response_model=ContextEntityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register or update a context entry",
)
async def create_context_entry(
    body: ContextCreateRequest,
    _user=Depends(get_current_user),
    manager: ContextManager = Depends(_manager),
):
    """
    Create a new context entry or bump version if context type exists.
    """
    return await manager.create_or_update_context(body)


@router.get(
    "/{context_id}",
    response_model=ContextEntityResponse,
    summary="Retrieve context details by ID",
)
async def get_context_by_id(
    context_id: int,
    _user=Depends(get_current_user),
    manager: ContextManager = Depends(_manager),
):
    """
    Retrieve specific context entity by ID.
    """
    item = await manager.get_context(context_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Context {context_id} not found.",
        )
    return item


@router.put(
    "/{context_id}",
    response_model=ContextEntityResponse,
    summary="Update context payload and bump version",
)
async def update_context_entry(
    context_id: int,
    body: ContextCreateRequest,
    _user=Depends(get_current_user),
    manager: ContextManager = Depends(_manager),
):
    """
    Update context payload and increment version number.
    """
    return await manager.create_or_update_context(body)


@router.delete(
    "/{context_id}",
    summary="Invalidate / soft-delete a context entity",
)
async def delete_context_entry(
    context_id: int,
    _user=Depends(get_current_user),
    manager: ContextManager = Depends(_manager),
):
    """
    Mark context entity status as 'invalid'.
    """
    success = await manager.invalidate_context(context_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Context {context_id} not found.",
        )
    return {"detail": f"Context {context_id} invalidated successfully."}


# ── Context Validation Endpoint ───────────────────────────────────────────────

@router.post(
    "/validate",
    response_model=ContextValidationResponse,
    summary="Run validation checks on context bundle",
)
async def validate_context(
    project_id: int,
    agent_name: str = "system",
    _user=Depends(get_current_user),
    validator: ContextValidator = Depends(_validator),
    retrieval: ContextRetrievalService = Depends(_retrieval_service),
):
    """
    Validate contexts for missing, empty, invalid, duplicate, or corrupted entries.
    """
    bundle = await retrieval.retrieve_context_bundle(project_id, agent_name)
    return await validator.validate_bundle(project_id, agent_name, bundle)


# ── Context Scores & Metrics Endpoints ────────────────────────────────────────

@router.get(
    "/scores/{project_id}",
    response_model=ContextQualityScoreResponse,
    summary="Get 6-tier quality score metrics for project context",
)
async def get_context_scores(
    project_id: int,
    _user=Depends(get_current_user),
    scoring: ContextScoringService = Depends(_scoring_service),
    retrieval: ContextRetrievalService = Depends(_retrieval_service),
):
    """
    Return 6-tier quality scores: Relevancy, Confidence, Priority, Freshness, Source, Overall Quality.
    """
    bundle = await retrieval.retrieve_context_bundle(project_id, "system")
    return await scoring.evaluate_context_quality(project_id, bundle)


# ── Consumers, Producers & History Endpoints ─────────────────────────────────

@router.get(
    "/consumers/{project_id}",
    response_model=List[ContextHistoryRecord],
    summary="List context consumers and consumption log",
)
async def get_context_consumers(
    project_id: int,
    _user=Depends(get_current_user),
    history_manager: ContextHistoryManager = Depends(_history_manager),
):
    """
    Fetch history logs of context consumers.
    """
    history = await history_manager.get_project_history(project_id)
    return [h for h in history if h.consumer_agent is not None]


@router.get(
    "/producers/{project_id}",
    response_model=List[ContextHistoryRecord],
    summary="List context producers and creation log",
)
async def get_context_producers(
    project_id: int,
    _user=Depends(get_current_user),
    history_manager: ContextHistoryManager = Depends(_history_manager),
):
    """
    Fetch history logs of context producers.
    """
    history = await history_manager.get_project_history(project_id)
    return [h for h in history if h.action in ("created", "updated")]


@router.get(
    "/history/{project_id}",
    response_model=List[ContextHistoryRecord],
    summary="Get full context change and version history",
)
async def get_context_history(
    project_id: int,
    _user=Depends(get_current_user),
    history_manager: ContextHistoryManager = Depends(_history_manager),
):
    """
    Retrieve full audit log of context creations, updates, consumers, and invalidations.
    """
    return await history_manager.get_project_history(project_id)


# ── Visualization & Reports Endpoints ────────────────────────────────────────

@router.get(
    "/visualization/{project_id}",
    response_model=ContextVisualizationResponse,
    summary="Get context flow graph visualization data",
)
async def get_context_visualization(
    project_id: int,
    _user=Depends(get_current_user),
    flow_gen: ContextFlowGenerator = Depends(_flow_generator),
):
    """
    Return nodes and edges for frontend context flow graph component.
    """
    return await flow_gen.generate_visualization_data(project_id)


@router.get(
    "/reports/{project_id}",
    response_model=ContextReportResponse,
    summary="Get project context audit report",
)
async def get_context_report(
    project_id: int,
    _user=Depends(get_current_user),
    retrieval: ContextRetrievalService = Depends(_retrieval_service),
    scoring: ContextScoringService = Depends(_scoring_service),
):
    """
    Get detailed project-level context audit report.
    """
    items = await retrieval.list_project_contexts(project_id)
    bundle = await retrieval.retrieve_context_bundle(project_id, "system")
    score = await scoring.evaluate_context_quality(project_id, bundle)

    return ContextReportResponse(
        project_id=project_id,
        total_contexts=len(items),
        valid_contexts=len([i for i in items if i["status"] == "valid"]),
        invalid_contexts=len([i for i in items if i["status"] != "valid"]),
        average_quality_score=score.overall_quality_score,
        summary={"active_types": list(bundle.keys())},
    )


@router.post(
    "/reports/{project_id}",
    response_model=ContextReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate/re-calculate project context report",
)
async def generate_context_report(
    project_id: int,
    _user=Depends(get_current_user),
    retrieval: ContextRetrievalService = Depends(_retrieval_service),
    scoring: ContextScoringService = Depends(_scoring_service),
):
    """
    Re-calculate and return project context audit report.
    """
    return await get_context_report(project_id, _user, retrieval, scoring)
