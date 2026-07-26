"""
Memory API Router — Phase 3.4

Endpoints
---------
POST   /projects/{project_id}/memory/artifacts           Store an artifact
POST   /projects/{project_id}/memory/files               Store a generated file
POST   /projects/{project_id}/memory/revisions           Record a revision
POST   /projects/{project_id}/memory/search              Semantic search
GET    /projects/{project_id}/memory/history             Version history
GET    /projects/{project_id}/memory/agents/{agent_name} Agent memory records
GET    /projects/{project_id}/memory/files               Generated files list
GET    /projects/{project_id}/memory/revisions           Revision list
GET    /projects/{project_id}/memory/snapshot            Full project snapshot
DELETE /projects/{project_id}/memory                     Wipe project memory

All endpoints require JWT authentication (same auth dependency as the
existing projects router).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.api.auth import get_current_user
from memory.project_memory import ProjectMemoryService
from memory.schemas import (
    GeneratedFileRecord,
    MemorySearchRequest,
    ProjectSnapshot,
    RevisionEntry,
    StoreArtifactRequest,
    StoreRevisionRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/projects/{project_id}/memory",
    tags=["memory"],
)


# ---------------------------------------------------------------------------
# Dependency — one ProjectMemoryService per request (singleton under the hood)
# ---------------------------------------------------------------------------

def get_project_memory_service() -> ProjectMemoryService:
    """FastAPI dependency that returns the default ProjectMemoryService."""
    return ProjectMemoryService()


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class StoreResponse(BaseModel):
    memory_id: str
    project_id: int
    message: str


class StoreFileRequest(BaseModel):
    """Request body for POST /projects/{id}/memory/files."""
    file_path: str
    content: str
    language: str = "python"
    agent_name: str = "backend_developer"
    version: int = 1


class SearchResponse(BaseModel):
    project_id: int
    query: str
    results: List[Dict[str, Any]]
    total: int


class VersionHistoryResponse(BaseModel):
    project_id: int
    artifact_type: Optional[str]
    entries: List[Dict[str, Any]]
    total: int


class AgentMemoryResponse(BaseModel):
    project_id: int
    agent_name: str
    records: List[Dict[str, Any]]
    total: int


# ---------------------------------------------------------------------------
# Store artifact
# ---------------------------------------------------------------------------

@router.post(
    "/artifacts",
    response_model=StoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Store a project artifact in memory",
)
async def store_artifact(
    project_id: int,
    body: StoreArtifactRequest,
    _user=Depends(get_current_user),
    pms: ProjectMemoryService = Depends(get_project_memory_service),
) -> StoreResponse:
    """Store any agent artifact and version it in project_history."""
    try:
        mem_id = pms.store_agent_output(
            project_id=project_id,
            agent_name=body.agent_name,
            artifact_type=body.artifact_type,
            content=body.content,
            version=body.version,
        )
        return StoreResponse(
            memory_id=mem_id,
            project_id=project_id,
            message="Artifact stored successfully.",
        )
    except Exception as exc:
        logger.error("[MEMORY API] store_artifact failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store artifact: {exc}",
        )


# ---------------------------------------------------------------------------
# Store generated file
# ---------------------------------------------------------------------------

@router.post(
    "/files",
    response_model=StoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a generated source file",
)
async def store_file(
    project_id: int,
    body: StoreFileRequest,
    _user=Depends(get_current_user),
    pms: ProjectMemoryService = Depends(get_project_memory_service),
) -> StoreResponse:
    """Track a generated source file with its path and language."""
    try:
        mem_id = pms.store_generated_file(
            project_id=project_id,
            file_path=body.file_path,
            content=body.content,
            language=body.language,
            agent_name=body.agent_name,
            version=body.version,
        )
        return StoreResponse(
            memory_id=mem_id,
            project_id=project_id,
            message="Generated file stored successfully.",
        )
    except Exception as exc:
        logger.error("[MEMORY API] store_file failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store generated file: {exc}",
        )


# ---------------------------------------------------------------------------
# Record revision
# ---------------------------------------------------------------------------

@router.post(
    "/revisions",
    response_model=StoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a tracked revision",
)
async def record_revision(
    project_id: int,
    body: StoreRevisionRequest,
    _user=Depends(get_current_user),
    pms: ProjectMemoryService = Depends(get_project_memory_service),
) -> StoreResponse:
    """Append a revision record with an optional reason and author."""
    try:
        mem_id = pms.record_revision(
            project_id=project_id,
            artifact_type=body.artifact_type,
            content=body.content,
            version=body.version,
            reason=body.reason,
            requested_by=body.requested_by,
        )
        return StoreResponse(
            memory_id=mem_id,
            project_id=project_id,
            message="Revision recorded successfully.",
        )
    except Exception as exc:
        logger.error("[MEMORY API] record_revision failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record revision: {exc}",
        )


# ---------------------------------------------------------------------------
# Semantic search
# ---------------------------------------------------------------------------

@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Semantic search across project memory",
)
async def search_memory(
    project_id: int,
    body: MemorySearchRequest,
    _user=Depends(get_current_user),
    pms: ProjectMemoryService = Depends(get_project_memory_service),
) -> SearchResponse:
    """Cross-collection semantic search scoped to this project."""
    results = pms.search_project_memory(
        project_id=project_id,
        query=body.query,
        collections=body.collections,
        limit=body.limit,
        threshold=body.threshold,
    )
    return SearchResponse(
        project_id=project_id,
        query=body.query,
        results=results,
        total=len(results),
    )


# ---------------------------------------------------------------------------
# Version history
# ---------------------------------------------------------------------------

@router.get(
    "/history",
    response_model=VersionHistoryResponse,
    summary="Get version history for a project",
)
async def get_version_history(
    project_id: int,
    artifact_type: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    _user=Depends(get_current_user),
    pms: ProjectMemoryService = Depends(get_project_memory_service),
) -> VersionHistoryResponse:
    """Fetch all versioned snapshots for a project."""
    entries = pms.get_version_history(
        project_id=project_id,
        artifact_type=artifact_type,
        limit=limit,
    )
    return VersionHistoryResponse(
        project_id=project_id,
        artifact_type=artifact_type,
        entries=[e.model_dump() for e in entries],
        total=len(entries),
    )


# ---------------------------------------------------------------------------
# Agent memory
# ---------------------------------------------------------------------------

@router.get(
    "/agents/{agent_name}",
    response_model=AgentMemoryResponse,
    summary="Get all memory records for a specific agent",
)
async def get_agent_memory(
    project_id: int,
    agent_name: str,
    collection_name: Optional[str] = Query(default=None),
    _user=Depends(get_current_user),
    pms: ProjectMemoryService = Depends(get_project_memory_service),
) -> AgentMemoryResponse:
    """Return all stored outputs for a given agent in this project."""
    records = pms.get_agent_memory(
        project_id=project_id,
        agent_name=agent_name,
        collection_name=collection_name,
    )
    return AgentMemoryResponse(
        project_id=project_id,
        agent_name=agent_name,
        records=[r.model_dump() for r in records],
        total=len(records),
    )


# ---------------------------------------------------------------------------
# Generated files
# ---------------------------------------------------------------------------

@router.get(
    "/files",
    response_model=List[Dict[str, Any]],
    summary="List all generated files for a project",
)
async def list_generated_files(
    project_id: int,
    _user=Depends(get_current_user),
    pms: ProjectMemoryService = Depends(get_project_memory_service),
) -> List[Dict[str, Any]]:
    """List all generated source files recorded for this project."""
    files = pms.get_generated_files(project_id=project_id)
    return [f.model_dump() for f in files]


# ---------------------------------------------------------------------------
# Revisions
# ---------------------------------------------------------------------------

@router.get(
    "/revisions",
    response_model=List[Dict[str, Any]],
    summary="List revisions for a project",
)
async def list_revisions(
    project_id: int,
    artifact_type: Optional[str] = Query(default=None),
    _user=Depends(get_current_user),
    pms: ProjectMemoryService = Depends(get_project_memory_service),
) -> List[Dict[str, Any]]:
    """Return all tracked revisions for this project."""
    revisions = pms.get_revisions(
        project_id=project_id,
        artifact_type=artifact_type,
    )
    return [r.model_dump() for r in revisions]


# ---------------------------------------------------------------------------
# Full project snapshot
# ---------------------------------------------------------------------------

@router.get(
    "/snapshot",
    response_model=Dict[str, Any],
    summary="Full project memory snapshot",
)
async def get_snapshot(
    project_id: int,
    _user=Depends(get_current_user),
    pms: ProjectMemoryService = Depends(get_project_memory_service),
) -> Dict[str, Any]:
    """Return a complete point-in-time snapshot of all project memory."""
    snapshot = pms.get_project_snapshot(project_id=project_id)
    return snapshot.model_dump()


# ---------------------------------------------------------------------------
# Delete project memory
# ---------------------------------------------------------------------------

@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Wipe all memory for a project",
)
async def delete_project_memory(
    project_id: int,
    _user=Depends(get_current_user),
    pms: ProjectMemoryService = Depends(get_project_memory_service),
) -> None:
    """Permanently delete all memory records for this project."""
    try:
        pms._svc.delete_project_memory(project_id=project_id)
        logger.info("[MEMORY API] Deleted all memory for project %d", project_id)
    except Exception as exc:
        logger.error("[MEMORY API] delete failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project memory: {exc}",
        )
