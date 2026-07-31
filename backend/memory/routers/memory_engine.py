"""
Domain Memory Engine Router — Phase 5.1

Generic, domain-parameterised REST endpoints for all 12 memory engines.
Uses a ``{domain}`` path parameter to resolve the correct engine at
runtime, keeping the router DRY while supporting full CRUD, search,
versioning, and similarity retrieval for every domain.

Endpoints
---------
POST   /memory-engine/{domain}/projects/{project_id}/entries               Create
GET    /memory-engine/{domain}/projects/{project_id}/entries               List
GET    /memory-engine/{domain}/projects/{project_id}/entries/{entry_id}    Get
PUT    /memory-engine/{domain}/projects/{project_id}/entries/{entry_id}    Update
DELETE /memory-engine/{domain}/projects/{project_id}/entries/{entry_id}    Delete
POST   /memory-engine/{domain}/projects/{project_id}/search               Search
GET    /memory-engine/{domain}/projects/{project_id}/entries/{entry_id}/versions   Versions
POST   /memory-engine/{domain}/projects/{project_id}/similar              Similarity
GET    /memory-engine/{domain}/projects/{project_id}/summary              Summary
GET    /memory-engine/domains                                             List domains
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.security import get_current_user
from memory.persistent_schemas import (
    PersistentMemoryResponse,
    PersistentMemoryVersionResponse,
)
from memory.services import ENGINE_REGISTRY, get_engine
from memory.services.base_memory_service import BaseMemoryEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/memory-engine", tags=["memory-engine"])


# ── Request / Response schemas ──────────────────────────────────────────────


class EngineCreateRequest(BaseModel):
    """Generic create request for any domain memory engine."""
    content: str = Field(..., min_length=1)
    agent_name: str = Field(default="system")
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    domain_fields: Dict[str, Any] = Field(
        default_factory=dict,
        description="Domain-specific fields stored in metadata_json",
    )
    version: int = Field(default=1, ge=1)


class EngineUpdateRequest(BaseModel):
    """Generic update request for any domain memory engine."""
    content: str = Field(..., min_length=1)
    metadata_json: Optional[Dict[str, Any]] = None
    domain_fields: Dict[str, Any] = Field(default_factory=dict)
    change_reason: str = Field(default="")
    changed_by: str = Field(default="system")


class EngineSearchRequest(BaseModel):
    """Search request for a domain memory engine."""
    query: str = Field(..., min_length=1)
    limit: int = Field(default=50, ge=1, le=500)


class EngineSimilarityRequest(BaseModel):
    """Similarity retrieval request for ChromaDB vectors."""
    query: str = Field(..., min_length=1)
    limit: int = Field(default=5, ge=1, le=100)
    threshold: float = Field(default=0.0, ge=0.0, le=1.0)


class EngineSearchResponse(BaseModel):
    """Search result response."""
    domain: str
    project_id: int
    query: str
    results: List[PersistentMemoryResponse]
    total: int


class EngineListResponse(BaseModel):
    """List response for a domain engine."""
    domain: str
    project_id: int
    entries: List[PersistentMemoryResponse]
    total: int


class EngineDeleteResponse(BaseModel):
    """Deletion response."""
    message: str
    entry_id: int
    domain: str


class EngineSummaryResponse(BaseModel):
    """Summary response from a domain engine."""
    domain: str
    project_id: int
    total_entries: int


class EngineSimilarityResponse(BaseModel):
    """Similarity search results from ChromaDB."""
    domain: str
    project_id: int
    query: str
    results: List[Dict[str, Any]]
    total: int


class DomainsListResponse(BaseModel):
    """List of all available memory domains."""
    domains: List[str]
    total: int


# ── Dependency ──────────────────────────────────────────────────────────────


def _resolve_engine(domain: str) -> BaseMemoryEngine:
    """Resolve domain path param to an engine instance, or raise 404."""
    try:
        return get_engine(domain)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


# ── Endpoints ───────────────────────────────────────────────────────────────


@router.get(
    "/domains",
    response_model=DomainsListResponse,
    summary="List all available memory domains",
)
async def list_domains(_user=Depends(get_current_user)):
    """Return the list of all registered memory domains."""
    domains = sorted(ENGINE_REGISTRY.keys())
    return DomainsListResponse(domains=domains, total=len(domains))


@router.post(
    "/{domain}/projects/{project_id}/entries",
    response_model=PersistentMemoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a domain memory entry",
)
async def create_entry(
    domain: str,
    project_id: int,
    body: EngineCreateRequest,
    _user=Depends(get_current_user),
):
    """Create a new memory entry in the specified domain engine."""
    engine = _resolve_engine(domain)
    return await engine.create(
        project_id=project_id,
        content=body.content,
        agent_name=body.agent_name,
        metadata_json=body.metadata_json,
        domain_fields=body.domain_fields,
        version=body.version,
    )


@router.get(
    "/{domain}/projects/{project_id}/entries",
    response_model=EngineListResponse,
    summary="List domain memory entries",
)
async def list_entries(
    domain: str,
    project_id: int,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _user=Depends(get_current_user),
):
    """List all active entries for a domain engine."""
    engine = _resolve_engine(domain)
    entries = await engine.list_entries(
        project_id=project_id, limit=limit, offset=offset,
    )
    return EngineListResponse(
        domain=domain,
        project_id=project_id,
        entries=entries,
        total=len(entries),
    )


@router.get(
    "/{domain}/projects/{project_id}/entries/{entry_id}",
    response_model=PersistentMemoryResponse,
    summary="Get a single domain memory entry",
)
async def get_entry(
    domain: str,
    project_id: int,
    entry_id: int,
    _user=Depends(get_current_user),
):
    """Return a specific memory entry by ID, scoped to the domain."""
    engine = _resolve_engine(domain)
    entry = await engine.get(project_id=project_id, entry_id=entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Memory entry not found")
    return entry


@router.put(
    "/{domain}/projects/{project_id}/entries/{entry_id}",
    response_model=PersistentMemoryResponse,
    summary="Update a domain memory entry (creates new version)",
)
async def update_entry(
    domain: str,
    project_id: int,
    entry_id: int,
    body: EngineUpdateRequest,
    _user=Depends(get_current_user),
):
    """Update content and/or metadata.  Automatically increments version."""
    engine = _resolve_engine(domain)
    entry = await engine.update(
        project_id=project_id,
        entry_id=entry_id,
        content=body.content,
        metadata_json=body.metadata_json,
        domain_fields=body.domain_fields,
        change_reason=body.change_reason,
        changed_by=body.changed_by,
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Memory entry not found")
    return entry


@router.delete(
    "/{domain}/projects/{project_id}/entries/{entry_id}",
    response_model=EngineDeleteResponse,
    summary="Soft-delete a domain memory entry",
)
async def delete_entry(
    domain: str,
    project_id: int,
    entry_id: int,
    _user=Depends(get_current_user),
):
    """Mark a memory entry as inactive (soft delete)."""
    engine = _resolve_engine(domain)
    deleted = await engine.delete(project_id=project_id, entry_id=entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory entry not found")
    return EngineDeleteResponse(
        message="Memory entry deleted successfully",
        entry_id=entry_id,
        domain=domain,
    )


@router.post(
    "/{domain}/projects/{project_id}/search",
    response_model=EngineSearchResponse,
    summary="Search domain memory entries",
)
async def search_entries(
    domain: str,
    project_id: int,
    body: EngineSearchRequest,
    _user=Depends(get_current_user),
):
    """Full-text search across memory entries in the specified domain."""
    engine = _resolve_engine(domain)
    results = await engine.search(
        project_id=project_id,
        query=body.query,
        limit=body.limit,
    )
    return EngineSearchResponse(
        domain=domain,
        project_id=project_id,
        query=body.query,
        results=results,
        total=len(results),
    )


@router.get(
    "/{domain}/projects/{project_id}/entries/{entry_id}/versions",
    response_model=List[PersistentMemoryVersionResponse],
    summary="Get version history for a domain entry",
)
async def get_version_history(
    domain: str,
    project_id: int,
    entry_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    _user=Depends(get_current_user),
):
    """Return all versions of a memory entry, newest first."""
    engine = _resolve_engine(domain)
    versions = await engine.get_versions(
        project_id=project_id, entry_id=entry_id, limit=limit,
    )
    if not versions:
        entry = await engine.get(project_id=project_id, entry_id=entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Memory entry not found")
    return versions


@router.post(
    "/{domain}/projects/{project_id}/similar",
    response_model=EngineSimilarityResponse,
    summary="Similarity search via ChromaDB vectors",
)
async def find_similar(
    domain: str,
    project_id: int,
    body: EngineSimilarityRequest,
    _user=Depends(get_current_user),
):
    """Semantic similarity search using ChromaDB vector store."""
    engine = _resolve_engine(domain)
    results = await engine.find_similar(
        project_id=project_id,
        query=body.query,
        limit=body.limit,
        threshold=body.threshold,
    )
    return EngineSimilarityResponse(
        domain=domain,
        project_id=project_id,
        query=body.query,
        results=results,
        total=len(results),
    )


@router.get(
    "/{domain}/projects/{project_id}/summary",
    response_model=EngineSummaryResponse,
    summary="Get summary of entries for a domain",
)
async def get_summary(
    domain: str,
    project_id: int,
    _user=Depends(get_current_user),
):
    """Return a count summary for the specified domain engine."""
    engine = _resolve_engine(domain)
    count = await engine.count(project_id=project_id)
    return EngineSummaryResponse(
        domain=domain,
        project_id=project_id,
        total_entries=count,
    )
