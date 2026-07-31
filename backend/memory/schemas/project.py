"""
Project memory schemas — Phase 5.1

Pydantic data contracts for the Project Memory Engine.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProjectMemoryCreate(BaseModel):
    """Create a project-level memory entry."""
    content: str = Field(..., min_length=1)
    agent_name: str = Field(default="system")
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    # Domain-specific fields stored in metadata_json
    project_phase: Optional[str] = Field(default=None, description="Current project phase")
    milestone: Optional[str] = Field(default=None, description="Associated milestone")
    status: Optional[str] = Field(default=None, description="Project status")
    priority: Optional[str] = Field(default=None, description="Priority level")
    tags: Optional[List[str]] = Field(default=None, description="Categorization tags")


class ProjectMemoryUpdate(BaseModel):
    """Update a project-level memory entry."""
    content: str = Field(..., min_length=1)
    metadata_json: Optional[Dict[str, Any]] = None
    change_reason: str = Field(default="")
    changed_by: str = Field(default="system")
    project_phase: Optional[str] = None
    milestone: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    tags: Optional[List[str]] = None


class ProjectMemoryResponse(BaseModel):
    """Response for a project memory entry."""
    id: int
    project_id: int
    category: str
    agent_name: str
    content: str
    metadata_json: Dict[str, Any]
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Extracted domain fields
    project_phase: Optional[str] = None
    milestone: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    tags: Optional[List[str]] = None

    model_config = {"from_attributes": True}


class ProjectMemorySearchResult(BaseModel):
    """Search result for project memory."""
    entries: List[ProjectMemoryResponse]
    total: int
    query: str
