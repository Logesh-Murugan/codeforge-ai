"""
Validation Engine FastAPI Router — Phase 4.2

Endpoints
---------
POST /validate/projects/{project_id}          Run full validation
GET  /validate/projects/{project_id}/report   Get latest validation report
POST /validate/projects/{project_id}/category Run a single category
"""
from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.security import get_current_user
from validation_engine.schemas import ValidationReport, ValidationRequest
from validation_engine.engine import ValidationEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/validate", tags=["validation"])


class SingleCategoryRequest(BaseModel):
    category: str


@router.post(
    "/projects/{project_id}",
    response_model=ValidationReport,
    summary="Run full project validation",
)
async def validate_project(
    project_id: int,
    request: Optional[ValidationRequest] = None,
    _user=Depends(get_current_user),
):
    """
    Validate a generated project across all six categories.
    Returns a ValidationReport with PASS/FAIL, score, errors, warnings, and recommendations.
    """
    from app.db import AsyncSessionLocal
    from sqlalchemy import select
    from app.models import Project, AgentRun

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Project).where(Project.id == project_id, Project.owner_id == _user.id)
        )
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        result2 = await session.execute(
            select(AgentRun).where(AgentRun.project_id == project_id)
        )
        agent_runs = result2.scalars().all()

    generated_files = project.generated_files or []
    agent_outputs = {r.agent_name: r.output_json or {} for r in agent_runs}
    categories = request.categories if request else None

    engine = ValidationEngine()
    report = engine.validate_from_bundle(
        project_id=project_id,
        project_title=project.title,
        generated_files=generated_files,
        agent_outputs=agent_outputs,
        categories=categories,
    )
    return report


@router.post(
    "/projects/{project_id}/category",
    response_model=ValidationReport,
    summary="Run validation for a single category",
)
async def validate_category(
    project_id: int,
    body: SingleCategoryRequest,
    _user=Depends(get_current_user),
):
    """Run validation for one specific category only."""
    from app.db import AsyncSessionLocal
    from sqlalchemy import select
    from app.models import Project, AgentRun

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Project).where(Project.id == project_id, Project.owner_id == _user.id)
        )
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        result2 = await session.execute(
            select(AgentRun).where(AgentRun.project_id == project_id)
        )
        agent_runs = result2.scalars().all()

    generated_files = project.generated_files or []
    agent_outputs = {r.agent_name: r.output_json or {} for r in agent_runs}

    engine = ValidationEngine()
    report = engine.validate_from_bundle(
        project_id=project_id,
        project_title=project.title,
        generated_files=generated_files,
        agent_outputs=agent_outputs,
        categories=[body.category],
    )
    return report
