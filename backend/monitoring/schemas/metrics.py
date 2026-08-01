"""
Metrics Schemas — Phase 5.7
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MonitoringMetricsResponse(BaseModel):
    project_id: int
    total_execution_time_ms: float = Field(default=0.0)
    avg_agent_runtime_ms: float = Field(default=0.0)
    workflow_runtime_ms: float = Field(default=0.0)
    total_retries: int = Field(default=0)
    success_rate_pct: float = Field(default=100.0)
    failure_rate_pct: float = Field(default=0.0)
    token_estimate: int = Field(default=0)
    generated_files_count: int = Field(default=0)
    current_provider: str = Field(default="groq")
    current_model: str = Field(default="llama-3.1-8b")
    current_embedding: str = Field(default="all-MiniLM-L6-v2")
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
