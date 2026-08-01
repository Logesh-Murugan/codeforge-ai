"""
Monitoring Events Schemas — Phase 5.7
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class MonitoringEventType(str, Enum):
    WORKFLOW_STARTED = "WorkflowStarted"
    WORKFLOW_COMPLETED = "WorkflowCompleted"
    WORKFLOW_FAILED = "WorkflowFailed"
    WORKFLOW_CANCELLED = "WorkflowCancelled"
    AGENT_STARTED = "AgentStarted"
    AGENT_FINISHED = "AgentFinished"
    AGENT_FAILED = "AgentFailed"
    RETRY_STARTED = "RetryStarted"
    RETRY_FINISHED = "RetryFinished"
    VALIDATION_STARTED = "ValidationStarted"
    VALIDATION_FINISHED = "ValidationFinished"
    EXPORT_STARTED = "ExportStarted"
    EXPORT_FINISHED = "ExportFinished"
    MEMORY_UPDATED = "MemoryUpdated"
    CONTEXT_UPDATED = "ContextUpdated"
    MODEL_SWITCHED = "ModelSwitched"
    PROVIDER_CHANGED = "ProviderChanged"


class MonitoringEventPayload(BaseModel):
    project_id: int
    event_type: MonitoringEventType
    agent_name: Optional[str] = None
    message: str = ""
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
