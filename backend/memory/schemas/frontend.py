"""
Frontend memory schemas — Phase 5.1

Pydantic data contracts for the Frontend Memory Engine.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FrontendMemoryCreate(BaseModel):
    """Create a frontend memory entry."""
    content: str = Field(..., min_length=1)
    agent_name: str = Field(default="frontend_developer")
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    file_path: Optional[str] = Field(default=None, description="Source file path")
    language: Optional[str] = Field(default="typescript", description="Programming language")
    framework: Optional[str] = Field(default=None, description="Framework: react/nextjs/vue/angular")
    component_name: Optional[str] = Field(default=None, description="Component name")
    component_type: Optional[str] = Field(default=None, description="page/layout/widget/hook/util")
    styling: Optional[str] = Field(default=None, description="Styling approach: css/tailwind/styled")
    route_path: Optional[str] = Field(default=None, description="Frontend route path")


class FrontendMemoryUpdate(BaseModel):
    """Update a frontend memory entry."""
    content: str = Field(..., min_length=1)
    metadata_json: Optional[Dict[str, Any]] = None
    change_reason: str = Field(default="")
    changed_by: str = Field(default="system")
    file_path: Optional[str] = None
    language: Optional[str] = None
    framework: Optional[str] = None
    component_name: Optional[str] = None
    component_type: Optional[str] = None
    styling: Optional[str] = None
    route_path: Optional[str] = None


class FrontendMemoryResponse(BaseModel):
    """Response for a frontend memory entry."""
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

    file_path: Optional[str] = None
    language: Optional[str] = None
    framework: Optional[str] = None
    component_name: Optional[str] = None
    component_type: Optional[str] = None
    styling: Optional[str] = None
    route_path: Optional[str] = None

    model_config = {"from_attributes": True}


class FrontendMemorySearchResult(BaseModel):
    """Search result for frontend memory."""
    entries: List[FrontendMemoryResponse]
    total: int
    query: str
