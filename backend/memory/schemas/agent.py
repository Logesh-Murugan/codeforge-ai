"""
Agent memory schemas — Phase 5.1

Pydantic data contracts for the Agent Memory Engine.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentMemoryCreate(BaseModel):
    """Create an agent-specific memory entry."""
    content: str = Field(..., min_length=1)
    agent_name: str = Field(..., min_length=1)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    agent_type: Optional[str] = Field(default="general", description="Agent classification")
    task_context: Optional[str] = Field(default=None, description="Task the agent was performing")
    output_summary: Optional[str] = Field(default=None, description="Summary of agent output")
    model_used: Optional[str] = Field(default=None, description="LLM model used")
    execution_duration_ms: Optional[float] = Field(default=None, description="Execution time in ms")
    token_count: Optional[int] = Field(default=None, description="Tokens consumed")


class AgentMemoryUpdate(BaseModel):
    """Update an agent memory entry."""
    content: str = Field(..., min_length=1)
    metadata_json: Optional[Dict[str, Any]] = None
    change_reason: str = Field(default="")
    changed_by: str = Field(default="system")
    task_context: Optional[str] = None
    output_summary: Optional[str] = None


class AgentMemoryResponse(BaseModel):
    """Response for an agent memory entry."""
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

    agent_type: Optional[str] = None
    task_context: Optional[str] = None
    output_summary: Optional[str] = None
    model_used: Optional[str] = None
    execution_duration_ms: Optional[float] = None
    token_count: Optional[int] = None

    model_config = {"from_attributes": True}


class AgentMemorySearchResult(BaseModel):
    """Search result for agent memory."""
    entries: List[AgentMemoryResponse]
    total: int
    query: str
