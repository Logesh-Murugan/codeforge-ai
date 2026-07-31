"""
Documentation memory schemas — Phase 5.1

Pydantic data contracts for the Documentation Memory Engine.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DocumentationMemoryCreate(BaseModel):
    """Create a documentation memory entry."""
    content: str = Field(..., min_length=1)
    agent_name: str = Field(default="doc_writer")
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    doc_type: Optional[str] = Field(default=None, description="readme/api-docs/guide/changelog/adr")
    audience: Optional[str] = Field(default=None, description="developer/user/admin/stakeholder")
    doc_format: Optional[str] = Field(default=None, description="markdown/rst/html/openapi")
    sections: Optional[List[str]] = Field(default=None, description="Document section titles")
    related_files: Optional[List[str]] = Field(default=None, description="Files this doc covers")
    auto_generated: Optional[bool] = Field(default=None, description="Whether auto-generated")


class DocumentationMemoryUpdate(BaseModel):
    """Update a documentation memory entry."""
    content: str = Field(..., min_length=1)
    metadata_json: Optional[Dict[str, Any]] = None
    change_reason: str = Field(default="")
    changed_by: str = Field(default="system")
    doc_type: Optional[str] = None
    audience: Optional[str] = None
    doc_format: Optional[str] = None
    sections: Optional[List[str]] = None
    related_files: Optional[List[str]] = None
    auto_generated: Optional[bool] = None


class DocumentationMemoryResponse(BaseModel):
    """Response for a documentation memory entry."""
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

    doc_type: Optional[str] = None
    audience: Optional[str] = None
    doc_format: Optional[str] = None
    sections: Optional[List[str]] = None
    related_files: Optional[List[str]] = None
    auto_generated: Optional[bool] = None

    model_config = {"from_attributes": True}


class DocumentationMemorySearchResult(BaseModel):
    """Search result for documentation memory."""
    entries: List[DocumentationMemoryResponse]
    total: int
    query: str
