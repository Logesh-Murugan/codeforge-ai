"""
Testing Engine FastAPI Router — Phase 4.4

Endpoints
---------
POST /testing/projects/{project_id}        Run full self-test pipeline
POST /testing/projects/{project_id}/run    Run specific tests
GET  /testing/projects/{project_id}/report Latest testing report (from memory)
"""
from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.security import get_current_user
from testing_engine.schemas import TestingReport
from testing_engine.engine import TestingEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/testing", tags=["testing"])


class RunTestsRequest(BaseModel):
    test_ids: Optional[List[str]] = None


@router.post(
    "/projects/{project_id}",
    response_model=TestingReport,
    summary="Run full self-test pipeline on a generated project",
)
async def run_self_tests(
    project_id: int,
    request: Optional[RunTestsRequest] = None,
    _user=Depends(get_current_user),
):
    """Run all 15 automated tests and return a TestingReport."""
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
    test_ids = request.test_ids if request else None

    engine = TestingEngine()
    return engine.run(
        project_id=project_id,
        project_title=project.title,
        generated_files=generated_files,
        agent_outputs=agent_outputs,
        test_ids=test_ids,
    )
