"""
Backend memory schemas — Phase 5.1

Pydantic data contracts for the Backend Memory Engine.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BackendMemoryCreate(BaseModel):
    """Create a backend memory entry."""
    content: str = Field(..., min_length=1)
    agent_name: str = Field(default="backend_developer")
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    file_path: Optional[str] = Field(default=None, description="Source file path")
    language: Optional[str] = Field(default="python", description="Programming language")
    framework: Optional[str] = Field(default=None, description="Framework: fastapi/django/flask")
    module_name: Optional[str] = Field(default=None, description="Module or package name")
    dependencies: Optional[List[str]] = Field(default=None, description="Package dependencies")
    code_type: Optional[str] = Field(default=None, description="model/service/route/util/config")


class BackendMemoryUpdate(BaseModel):
    """Update a backend memory entry."""
    content: str = Field(..., min_length=1)
    metadata_json: Optional[Dict[str, Any]] = None
    change_reason: str = Field(default="")
    changed_by: str = Field(default="system")
    file_path: Optional[str] = None
    language: Optional[str] = None
    framework: Optional[str] = None
    module_name: Optional[str] = None
    dependencies: Optional[List[str]] = None
    code_type: Optional[str] = None


class BackendMemoryResponse(BaseModel):
    """Response for a backend memory entry."""
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
    module_name: Optional[str] = None
    dependencies: Optional[List[str]] = None
    code_type: Optional[str] = None

    model_config = {"from_attributes": True}


class BackendMemorySearchResult(BaseModel):
    """Search result for backend memory."""
    entries: List[BackendMemoryResponse]
    total: int
    query: str
