"""
Workflow & Agent Status Schemas — Phase 5.7
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentStatus(str, Enum):
    WAITING = "waiting"
    RUNNING = "running"
    RETRYING = "retrying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentExecutionDTO(BaseModel):
    agent_name: str
    status: AgentStatus = Field(default=AgentStatus.WAITING)
    execution_time_ms: float = Field(default=0.0)
    retry_count: int = Field(default=0)
    current_task: Optional[str] = None
    input_size: int = Field(default=0)
    output_size: int = Field(default=0)
    generated_files_count: int = Field(default=0)
    validation_score: float = Field(default=1.0)
    security_score: float = Field(default=1.0)
    documentation_score: float = Field(default=1.0)
    quality_score: float = Field(default=1.0)


class WorkflowStatusDTO(BaseModel):
    project_id: int
    status: WorkflowStatus = Field(default=WorkflowStatus.PENDING)
    current_agent: Optional[str] = None
    completed_steps: int = Field(default=0)
    total_steps: int = Field(default=13)
    progress_pct: float = Field(default=0.0)
    execution_duration_ms: float = Field(default=0.0)
    estimated_remaining_ms: float = Field(default=0.0)
    retry_count: int = Field(default=0)
    agents: List[AgentExecutionDTO] = Field(default_factory=list)
