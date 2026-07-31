"""
Database memory schemas — Phase 5.1

Pydantic data contracts for the Database Memory Engine.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DatabaseMemoryCreate(BaseModel):
    """Create a database memory entry."""
    content: str = Field(..., min_length=1)
    agent_name: str = Field(default="database_engineer")
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    schema_definition: Optional[str] = Field(default=None, description="SQL schema DDL")
    table_name: Optional[str] = Field(default=None, description="Primary table name")
    relationships: Optional[List[str]] = Field(default=None, description="Table relationships")
    migration_status: Optional[str] = Field(default=None, description="pending/applied/rolled-back")
    db_engine: Optional[str] = Field(default=None, description="Database engine: postgresql/mysql/sqlite")
    indexes: Optional[List[str]] = Field(default=None, description="Index definitions")


class DatabaseMemoryUpdate(BaseModel):
    """Update a database memory entry."""
    content: str = Field(..., min_length=1)
    metadata_json: Optional[Dict[str, Any]] = None
    change_reason: str = Field(default="")
    changed_by: str = Field(default="system")
    schema_definition: Optional[str] = None
    table_name: Optional[str] = None
    relationships: Optional[List[str]] = None
    migration_status: Optional[str] = None
    db_engine: Optional[str] = None
    indexes: Optional[List[str]] = None


class DatabaseMemoryResponse(BaseModel):
    """Response for a database memory entry."""
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

    schema_definition: Optional[str] = None
    table_name: Optional[str] = None
    relationships: Optional[List[str]] = None
    migration_status: Optional[str] = None
    db_engine: Optional[str] = None
    indexes: Optional[List[str]] = None

    model_config = {"from_attributes": True}


class DatabaseMemorySearchResult(BaseModel):
    """Search result for database memory."""
    entries: List[DatabaseMemoryResponse]
    total: int
    query: str
