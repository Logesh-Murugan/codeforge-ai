"""
Export Engine FastAPI Router — Phase 4.1

Endpoints
---------
GET  /export/projects/{project_id}/zip          Full ZIP (source + reports)
GET  /export/projects/{project_id}/source-zip   Source code only
GET  /export/projects/{project_id}/reports-zip  Reports only
GET  /export/projects/{project_id}/report/{type} Single Markdown report
GET  /export/projects/{project_id}/summary       ExportResult metadata
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response, StreamingResponse
from io import BytesIO

from app.api.auth import get_current_user
from app.db import AsyncSessionLocal
from export_engine.schemas import (
    ExportResult,
    ProjectBundle,
    ReportType,
)
from export_engine.services.export_service import ExportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["export"])


# ---------------------------------------------------------------------------
# Dependency — one ExportService per request
# ---------------------------------------------------------------------------

def get_export_service() -> ExportService:
    return ExportService()


# ---------------------------------------------------------------------------
# Helper — load project + agent runs without importing DB in test mode
# ---------------------------------------------------------------------------

async def _load_bundle(project_id: int, session, current_user) -> ProjectBundle:
    """Load project data from DB and build a ProjectBundle."""
    from sqlalchemy import select
    from app.models import Project, AgentRun

    result = await session.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    result2 = await session.execute(
        select(AgentRun).where(AgentRun.project_id == project_id).order_by(AgentRun.created_at)
    )
    agent_runs = result2.scalars().all()

    svc = ExportService()
    return svc.build_bundle(
        project_id=project.id,
        project_title=project.title,
        project_description=project.description,
        project_status=project.status or "completed",
        agent_runs_raw=[
            {
                "agent_name": r.agent_name,
                "status": r.status,
                "output_json": r.output_json,
                "error_message": r.error_message,
                "created_at": r.created_at,
                "updated_at": r.updated_at,
            }
            for r in agent_runs
        ],
        generated_files_raw=project.generated_files or [],
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/projects/{project_id}/zip",
    summary="Download full project ZIP (source + all reports)",
    response_class=Response,
)
async def download_full_zip(
    project_id: int,
    current_user=Depends(get_current_user),
):
    """Returns a ZIP containing source code and all 12 professional reports."""
    async with AsyncSessionLocal() as session:
        bundle = await _load_bundle(project_id, session, current_user)

    svc = ExportService()
    zip_bytes = svc.export_zip(bundle)

    return StreamingResponse(
        BytesIO(zip_bytes),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="GeneratedProject_{project_id}.zip"'
        },
    )


@router.get(
    "/projects/{project_id}/source-zip",
    summary="Download source code only ZIP",
    response_class=Response,
)
async def download_source_zip(
    project_id: int,
    current_user=Depends(get_current_user),
):
    """Returns a ZIP containing only generated source code files."""
    async with AsyncSessionLocal() as session:
        bundle = await _load_bundle(project_id, session, current_user)

    svc = ExportService()
    zip_bytes = svc.export_source_zip(bundle)

    return StreamingResponse(
        BytesIO(zip_bytes),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="SourceCode_{project_id}.zip"'
        },
    )


@router.get(
    "/projects/{project_id}/reports-zip",
    summary="Download all project reports as ZIP",
    response_class=Response,
)
async def download_reports_zip(
    project_id: int,
    current_user=Depends(get_current_user),
):
    """Returns a ZIP containing all 12 Markdown reports."""
    async with AsyncSessionLocal() as session:
        bundle = await _load_bundle(project_id, session, current_user)

    svc = ExportService()
    zip_bytes = svc.export_reports_zip(bundle)

    return StreamingResponse(
        BytesIO(zip_bytes),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="Reports_{project_id}.zip"'
        },
    )


@router.get(
    "/projects/{project_id}/report/{report_type}",
    summary="Download a single Markdown report",
    response_class=Response,
)
async def download_single_report(
    project_id: int,
    report_type: ReportType,
    current_user=Depends(get_current_user),
):
    """Returns a single Markdown report file."""
    async with AsyncSessionLocal() as session:
        bundle = await _load_bundle(project_id, session, current_user)

    from export_engine.services.report_service import ReportService

    rs = ReportService()
    reports = rs.generate(bundle, [report_type])
    if not reports:
        raise HTTPException(status_code=404, detail="Report could not be generated")

    report = reports[0]
    return Response(
        content=report.content.encode(),
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="{report.filename}"'
        },
    )


@router.get(
    "/projects/{project_id}/summary",
    response_model=ExportResult,
    summary="Get export metadata summary",
)
async def get_export_summary(
    project_id: int,
    current_user=Depends(get_current_user),
):
    """Returns a summary of what would be exported for this project."""
    async with AsyncSessionLocal() as session:
        bundle = await _load_bundle(project_id, session, current_user)

    svc = ExportService()
    # Small zip just for size estimate
    zip_bytes = svc.export_zip(bundle)
    return svc.describe_export(bundle, zip_bytes)
