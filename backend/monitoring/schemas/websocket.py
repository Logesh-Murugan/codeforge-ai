"""
WebSocket Frame Schemas — Phase 5.7
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class WSFrameType(str, Enum):
    HEARTBEAT = "heartbeat"
    STATUS_UPDATE = "status_update"
    AGENT_EVENT = "agent_event"
    METRICS_UPDATE = "metrics_update"
    TIMELINE_UPDATE = "timeline_update"
    LOG_STREAM = "log_stream"


class WSFrame(BaseModel):
    type: WSFrameType
    project_id: int
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
