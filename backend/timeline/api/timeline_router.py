"""
Timeline Router — Phase 5.9

FastAPI route handlers for Project Timeline System.

Endpoints:
    GET  /timeline/{project_id}            Full chronological timeline
    GET  /timeline/history/{project_id}    Detailed execution event history
    GET  /timeline/milestones/{project_id} Milestone achievements & status
    GET  /timeline/statistics/{project_id} Project progress statistics
    GET  /timeline/analytics/{project_id}  Performance analytics breakdown
    GET  /timeline/report/{project_id}     Multi-format reports (MD, JSON, HTML)
    POST /timeline/event                   Record new event
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from timeline.reports.report_generator import report_generator
from timeline.schemas.timeline_schema import (
    MilestoneDTO,
    ProgressDTO,
    TimelineAnalyticsDTO,
    TimelineEventDTO,
)
from timeline.services.analytics_service import analytics_service
from timeline.services.milestone_service import milestone_service
from timeline.services.progress_service import progress_service
from timeline.services.timeline_service import timeline_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/timeline", tags=["project-timeline"])


@router.get(
    "/{project_id}",
    response_model=List[TimelineEventDTO],
    summary="Get full chronological timeline for a project",
)
async def get_project_timeline(
    project_id: int,
    _user=Depends(get_current_user),
):
    """Retrieve full timeline for project_id."""
    return await timeline_service.get_project_timeline(project_id)


@router.get(
    "/history/{project_id}",
    response_model=List[TimelineEventDTO],
    summary="Get detailed execution event history for a project",
)
async def get_timeline_history(
    project_id: int,
    _user=Depends(get_current_user),
):
    """Retrieve timeline event history for project_id."""
    return await timeline_service.get_project_timeline(project_id)


@router.get(
    "/milestones/{project_id}",
    response_model=List[MilestoneDTO],
    summary="Get milestones status & achievement timestamps for a project",
)
async def get_timeline_milestones(
    project_id: int,
    _user=Depends(get_current_user),
):
    """Retrieve project milestones."""
    return await milestone_service.get_project_milestones(project_id)


@router.get(
    "/statistics/{project_id}",
    response_model=ProgressDTO,
    summary="Get project progress & runtime statistics for a project",
)
async def get_timeline_statistics(
    project_id: int,
    _user=Depends(get_current_user),
):
    """Retrieve progress metrics for project_id."""
    return await progress_service.get_project_progress(project_id)


@router.get(
    "/analytics/{project_id}",
    response_model=TimelineAnalyticsDTO,
    summary="Get performance analytics breakdown for a project",
)
async def get_timeline_analytics(
    project_id: int,
    _user=Depends(get_current_user),
):
    """Retrieve performance analytics for project_id."""
    return await analytics_service.get_project_analytics(project_id)


@router.get(
    "/report/{project_id}",
    summary="Get multi-format timeline reports (MD, JSON, HTML)",
)
async def get_timeline_report(
    project_id: int,
    report_type: str = "summary",
    _user=Depends(get_current_user),
):
    """Retrieve generated Markdown, JSON, or HTML reports."""
    events = await timeline_service.get_project_timeline(project_id)
    reports = report_generator.generate_all_reports(events)
    return {
        "project_id": project_id,
        "report_type": report_type,
        "reports": reports,
    }


@router.post(
    "/event",
    response_model=TimelineEventDTO,
    summary="Record a new timeline event",
)
async def record_timeline_event(
    event: TimelineEventDTO,
    _user=Depends(get_current_user),
):
    """Record new event into timeline engine."""
    return await timeline_service.record_event(event)
