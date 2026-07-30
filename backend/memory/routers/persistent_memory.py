"""
Persistent Memory FastAPI Router — Phase 5.1

Endpoints
---------
POST   /pmemory/projects/{project_id}/entries              Create entry
GET    /pmemory/projects/{project_id}/entries               List entries
GET    /pmemory/projects/{project_id}/entries/{entry_id}     Get entry
PUT    /pmemory/projects/{project_id}/entries/{entry_id}     Update entry
DELETE /pmemory/projects/{project_id}/entries/{entry_id}     Delete entry
POST   /pmemory/projects/{project_id}/entries/search        Search entries
GET    /pmemory/projects/{project_id}/entries/{entry_id}/versions  Version history
GET    /pmemory/projects/{project_id}/categories/summary     Category summary
"""
from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import get_current_user
from memory.persistent_schemas import (
    CategorySummary,
    MemoryCategory,
    PersistentMemoryCreate,
    PersistentMemoryDeleteResponse,
    PersistentMemoryListResponse,
    PersistentMemoryResponse,
    PersistentMemorySearchRequest,
    PersistentMemorySearchResponse,
    PersistentMemorySummaryResponse,
    PersistentMemoryUpdate,
    PersistentMemoryVersionResponse,
)
from memory.persistent_service import PersistentMemoryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pmemory", tags=["persistent-memory"])


def get_pmemory_service() -> PersistentMemoryService:
    return PersistentMemoryService()


@router.post(
    "/projects/{project_id}/entries",
    response_model=PersistentMemoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a persistent memory entry",
)
async def create_entry(
    project_id: int,
    body: PersistentMemoryCreate,
    _user=Depends(get_current_user),
    svc: PersistentMemoryService = Depends(get_pmemory_service),
):
    """Store a new memory entry under a specific category."""
    return await svc.create_entry(
        project_id=project_id,
        category=body.category,
        content=body.content,
        agent_name=body.agent_name,
        metadata_json=body.metadata_json,
        version=body.version,
    )


@router.get(
    "/projects/{project_id}/entries",
    response_model=PersistentMemoryListResponse,
    summary="List persistent memory entries",
)
async def list_entries(
    project_id: int,
    category: Optional[MemoryCategory] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _user=Depends(get_current_user),
    svc: PersistentMemoryService = Depends(get_pmemory_service),
):
    """Retrieve all active memory entries, optionally filtered by category."""
    entries = await svc.list_entries(
        project_id=project_id,
        category=category,
        limit=limit,
        offset=offset,
    )
    return PersistentMemoryListResponse(
        project_id=project_id,
        category=category.value if category else None,
        entries=entries,
        total=len(entries),
    )


@router.get(
    "/projects/{project_id}/entries/{entry_id}",
    response_model=PersistentMemoryResponse,
    summary="Get a single memory entry",
)
async def get_entry(
    project_id: int,
    entry_id: int,
    _user=Depends(get_current_user),
    svc: PersistentMemoryService = Depends(get_pmemory_service),
):
    """Return a specific memory entry by ID."""
    entry = await svc.get_entry(project_id=project_id, entry_id=entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Memory entry not found")
    return entry


@router.put(
    "/projects/{project_id}/entries/{entry_id}",
    response_model=PersistentMemoryResponse,
    summary="Update a memory entry (creates a new version)",
)
async def update_entry(
    project_id: int,
    entry_id: int,
    body: PersistentMemoryUpdate,
    _user=Depends(get_current_user),
    svc: PersistentMemoryService = Depends(get_pmemory_service),
):
    """Update content and/or metadata. Automatically increments version."""
    entry = await svc.update_entry(
        project_id=project_id,
        entry_id=entry_id,
        content=body.content,
        metadata_json=body.metadata_json,
        change_reason=body.change_reason,
        changed_by=body.changed_by,
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Memory entry not found")
    return entry


@router.delete(
    "/projects/{project_id}/entries/{entry_id}",
    response_model=PersistentMemoryDeleteResponse,
    summary="Soft-delete a memory entry",
)
async def delete_entry(
    project_id: int,
    entry_id: int,
    _user=Depends(get_current_user),
    svc: PersistentMemoryService = Depends(get_pmemory_service),
):
    """Mark a memory entry as inactive (soft delete)."""
    deleted = await svc.delete_entry(project_id=project_id, entry_id=entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory entry not found")
    return PersistentMemoryDeleteResponse(
        message="Memory entry deleted successfully",
        entry_id=entry_id,
    )


@router.post(
    "/projects/{project_id}/entries/search",
    response_model=PersistentMemorySearchResponse,
    summary="Search memory entries by content",
)
async def search_entries(
    project_id: int,
    body: PersistentMemorySearchRequest,
    _user=Depends(get_current_user),
    svc: PersistentMemoryService = Depends(get_pmemory_service),
):
    """Full-text search across memory entry content and agent names."""
    entries = await svc.search_entries(
        project_id=project_id,
        query=body.query,
        category=body.category,
    )
    return PersistentMemorySearchResponse(
        project_id=project_id,
        query=body.query,
        results=entries,
        total=len(entries),
    )


@router.get(
    "/projects/{project_id}/entries/{entry_id}/versions",
    response_model=List[PersistentMemoryVersionResponse],
    summary="Get version history for an entry",
)
async def get_version_history(
    project_id: int,
    entry_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    _user=Depends(get_current_user),
    svc: PersistentMemoryService = Depends(get_pmemory_service),
):
    """Return all versions of a memory entry, newest first."""
    versions = await svc.get_version_history(
        project_id=project_id,
        entry_id=entry_id,
        limit=limit,
    )
    if not versions:
        # Check if entry exists at all
        entry = await svc.get_entry(project_id=project_id, entry_id=entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Memory entry not found")
    return versions


@router.get(
    "/projects/{project_id}/categories/summary",
    response_model=PersistentMemorySummaryResponse,
    summary="Summary of memory entries per category",
)
async def get_category_summary(
    project_id: int,
    _user=Depends(get_current_user),
    svc: PersistentMemoryService = Depends(get_pmemory_service),
):
    """Return counts and latest versions grouped by category."""
    categories = await svc.get_category_summary(project_id=project_id)
    total = await svc.count_entries(project_id=project_id)
    return PersistentMemorySummaryResponse(
        project_id=project_id,
        categories=categories,
        total_entries=total,
    )
