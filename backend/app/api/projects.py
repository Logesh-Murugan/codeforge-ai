import os
import zipfile
from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import get_session
from app.models import User, Project, AgentRun
from app.schemas import ProjectCreate, ProjectResponse, AgentRunResponse, GenerateProjectRequest
from app.core.security import get_current_user
from orchestrator.graph import run_pipeline

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    db_project = Project(
        title=project.title,
        description=project.description,
        owner_id=current_user.id
    )
    session.add(db_project)
    await session.commit()
    await session.refresh(db_project)
    return db_project


@router.get("", response_model=list[ProjectResponse])
async def get_projects(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    result = await session.execute(select(Project).where(Project.owner_id == current_user.id))
    return result.scalars().all()


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    result = await session.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    result = await session.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    await session.delete(project)
    await session.commit()
    return {"detail": "Project deleted successfully"}


@router.post("/{project_id}/generate")
async def generate_project(
    project_id: int,
    request: GenerateProjectRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Check project ownership
    result = await session.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    # Run pipeline in background
    background_tasks.add_task(run_pipeline, project_id, request.idea)
    
    return {"detail": "Project generation started"}


@router.get("/{project_id}/status", response_model=list[AgentRunResponse])
async def get_project_status(
    project_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Check project ownership
    result = await session.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    # Get agent runs
    result = await session.execute(
        select(AgentRun).where(AgentRun.project_id == project_id).order_by(AgentRun.created_at)
    )
    agent_runs = result.scalars().all()
    
    return agent_runs


@router.get("/{project_id}/download")
async def download_project(
    project_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Check project ownership
    result = await session.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    if not project.generated_files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Generated project files not found in database"
        )
    
    # Create zip file
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_info in project.generated_files:
            path = file_info["path"]
            content = file_info["content"]
            zipf.writestr(path, content)
    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=project_{project_id}.zip"}
    )
