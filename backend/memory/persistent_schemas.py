"""
Persistent Memory Pydantic schemas — Phase 5.1

Defines all public data contracts for the Persistent Project Memory Engine API.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MemoryCategory(str, Enum):
    PROJECT = "project"
    AGENT = "agent"
    REQUIREMENT = "requirement"
    ARCHITECTURE = "architecture"
    DATABASE = "database"
    API = "api"
    BACKEND = "backend"
    FRONTEND = "frontend"
    SECURITY = "security"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    DOCUMENTATION = "documentation"
    GENERATED_FILE = "generated_file"
    EXPORT = "export"


class PersistentMemoryCreate(BaseModel):
    category: MemoryCategory
    content: str = Field(..., min_length=1)
    agent_name: str = Field(default="system")
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    version: int = Field(default=1, ge=1)


class PersistentMemoryUpdate(BaseModel):
    content: str = Field(..., min_length=1)
    metadata_json: Optional[Dict[str, Any]] = None
    change_reason: str = Field(default="")
    changed_by: str = Field(default="system")


class PersistentMemoryResponse(BaseModel):
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

    model_config = {"from_attributes": True}


class PersistentMemoryVersionResponse(BaseModel):
    id: int
    entry_id: int
    project_id: int
    category: str
    content: str
    metadata_json: Dict[str, Any]
    version: int
    change_reason: str
    changed_by: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PersistentMemorySearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    category: Optional[MemoryCategory] = None


class PersistentMemorySearchResponse(BaseModel):
    project_id: int
    query: str
    results: List[PersistentMemoryResponse]
    total: int


class PersistentMemoryListResponse(BaseModel):
    project_id: int
    category: Optional[str]
    entries: List[PersistentMemoryResponse]
    total: int


class CategorySummary(BaseModel):
    category: str
    count: int
    latest_version: int
    last_updated: Optional[datetime] = None


class PersistentMemorySummaryResponse(BaseModel):
    project_id: int
    categories: List[CategorySummary]
    total_entries: int


class PersistentMemoryDeleteResponse(BaseModel):
    message: str
    entry_id: int
