"""
Requirement memory schemas — Phase 5.1

Pydantic data contracts for the Requirement Memory Engine.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RequirementMemoryCreate(BaseModel):
    """Create a requirement memory entry."""
    content: str = Field(..., min_length=1)
    agent_name: str = Field(default="business_analyst")
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    priority: Optional[str] = Field(default=None, description="Priority: critical/high/medium/low")
    status: Optional[str] = Field(default=None, description="Status: draft/approved/implemented")
    acceptance_criteria: Optional[List[str]] = Field(default=None, description="Acceptance criteria list")
    stakeholder: Optional[str] = Field(default=None, description="Requesting stakeholder")
    requirement_type: Optional[str] = Field(default=None, description="functional/non-functional/constraint")
    user_story: Optional[str] = Field(default=None, description="Associated user story")


class RequirementMemoryUpdate(BaseModel):
    """Update a requirement memory entry."""
    content: str = Field(..., min_length=1)
    metadata_json: Optional[Dict[str, Any]] = None
    change_reason: str = Field(default="")
    changed_by: str = Field(default="system")
    priority: Optional[str] = None
    status: Optional[str] = None
    acceptance_criteria: Optional[List[str]] = None
    stakeholder: Optional[str] = None
    requirement_type: Optional[str] = None


class RequirementMemoryResponse(BaseModel):
    """Response for a requirement memory entry."""
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

    priority: Optional[str] = None
    status: Optional[str] = None
    acceptance_criteria: Optional[List[str]] = None
    stakeholder: Optional[str] = None
    requirement_type: Optional[str] = None
    user_story: Optional[str] = None

    model_config = {"from_attributes": True}


class RequirementMemorySearchResult(BaseModel):
    """Search result for requirement memory."""
    entries: List[RequirementMemoryResponse]
    total: int
    query: str
