"""
Architecture memory schemas — Phase 5.1

Pydantic data contracts for the Architecture Memory Engine.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ArchitectureMemoryCreate(BaseModel):
    """Create an architecture memory entry."""
    content: str = Field(..., min_length=1)
    agent_name: str = Field(default="solution_architect")
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    component_name: Optional[str] = Field(default=None, description="Architecture component name")
    pattern: Optional[str] = Field(default=None, description="Design pattern used")
    tech_stack: Optional[List[str]] = Field(default=None, description="Technologies involved")
    layer: Optional[str] = Field(default=None, description="Architecture layer: presentation/business/data")
    diagram_url: Optional[str] = Field(default=None, description="URL to architecture diagram")
    decision_rationale: Optional[str] = Field(default=None, description="Why this approach was chosen")


class ArchitectureMemoryUpdate(BaseModel):
    """Update an architecture memory entry."""
    content: str = Field(..., min_length=1)
    metadata_json: Optional[Dict[str, Any]] = None
    change_reason: str = Field(default="")
    changed_by: str = Field(default="system")
    component_name: Optional[str] = None
    pattern: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    layer: Optional[str] = None
    diagram_url: Optional[str] = None
    decision_rationale: Optional[str] = None


class ArchitectureMemoryResponse(BaseModel):
    """Response for an architecture memory entry."""
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

    component_name: Optional[str] = None
    pattern: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    layer: Optional[str] = None
    diagram_url: Optional[str] = None
    decision_rationale: Optional[str] = None

    model_config = {"from_attributes": True}


class ArchitectureMemorySearchResult(BaseModel):
    """Search result for architecture memory."""
    entries: List[ArchitectureMemoryResponse]
    total: int
    query: str
