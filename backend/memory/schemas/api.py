"""
API memory schemas — Phase 5.1

Pydantic data contracts for the API Memory Engine.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class APIMemoryCreate(BaseModel):
    """Create an API memory entry."""
    content: str = Field(..., min_length=1)
    agent_name: str = Field(default="api_designer")
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    endpoint: Optional[str] = Field(default=None, description="API endpoint path")
    method: Optional[str] = Field(default=None, description="HTTP method: GET/POST/PUT/DELETE")
    request_schema: Optional[Dict[str, Any]] = Field(default=None, description="Request body schema")
    response_schema: Optional[Dict[str, Any]] = Field(default=None, description="Response body schema")
    auth_required: Optional[bool] = Field(default=None, description="Whether auth is required")
    api_version: Optional[str] = Field(default=None, description="API version string")
    rate_limit: Optional[str] = Field(default=None, description="Rate limiting config")


class APIMemoryUpdate(BaseModel):
    """Update an API memory entry."""
    content: str = Field(..., min_length=1)
    metadata_json: Optional[Dict[str, Any]] = None
    change_reason: str = Field(default="")
    changed_by: str = Field(default="system")
    endpoint: Optional[str] = None
    method: Optional[str] = None
    request_schema: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None
    auth_required: Optional[bool] = None
    api_version: Optional[str] = None
    rate_limit: Optional[str] = None


class APIMemoryResponse(BaseModel):
    """Response for an API memory entry."""
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

    endpoint: Optional[str] = None
    method: Optional[str] = None
    request_schema: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None
    auth_required: Optional[bool] = None
    api_version: Optional[str] = None
    rate_limit: Optional[str] = None

    model_config = {"from_attributes": True}


class APIMemorySearchResult(BaseModel):
    """Search result for API memory."""
    entries: List[APIMemoryResponse]
    total: int
    query: str
