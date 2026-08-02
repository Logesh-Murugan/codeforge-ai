"""
Timeline Schemas — Phase 5.9
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TimelineEventDTO(BaseModel):
    event_id: str
    project_id: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    agent_name: Optional[str] = None
    stage_name: Optional[str] = None
    status: str = "COMPLETED"
    duration_ms: float = 0.0
    retry_count: int = 0
    model_used: Optional[str] = None
    provider_used: Optional[str] = None
    execution_cost: float = 0.0
    execution_time_ms: float = 0.0
    generated_files_count: int = 0
    validation_score: float = 1.0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MilestoneDTO(BaseModel):
    project_id: int
    milestone_name: str
    status: str = "ACHIEVED"
    achieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    details: Dict[str, Any] = Field(default_factory=dict)


class ProgressDTO(BaseModel):
    project_id: int
    overall_progress_pct: float = 0.0
    current_stage: str = "Initialization"
    completed_stages_count: int = 0
    total_stages_count: int = 13
    estimated_time_remaining_ms: float = 0.0
    avg_agent_runtime_ms: float = 0.0
    avg_retry_count: float = 0.0
    avg_validation_score: float = 1.0


class TimelineAnalyticsDTO(BaseModel):
    project_id: int
    total_events: int = 0
    agent_performance: Dict[str, float] = Field(default_factory=dict)
    longest_stage: Optional[str] = None
    shortest_stage: Optional[str] = None
    total_retries: int = 0
    average_runtime_ms: float = 0.0
