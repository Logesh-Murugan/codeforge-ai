"""
Communication Schemas — Phase 5.4

Pydantic data models for inter-agent messaging and context exchange.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CommunicationPattern(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    VALIDATION = "validation"
    CONSENSUS = "consensus"
    FEEDBACK = "feedback"


class AgentMessageRequest(BaseModel):
    """Payload to record an inter-agent message or context transfer."""

    project_id: int = Field(..., description="Owning project ID.")
    sender_agent: str = Field(..., description="Agent sending context or output.")
    receiver_agent: str = Field(..., description="Agent receiving context or output.")
    pattern: CommunicationPattern = Field(
        default=CommunicationPattern.SEQUENTIAL,
        description="Communication pattern style.",
    )
    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Context, output, or review notes payload.",
    )


class AgentMessageResponse(BaseModel):
    """Response payload for a recorded inter-agent message."""

    log_id: int
    project_id: int
    sender_agent: str
    receiver_agent: str
    pattern: str
    status: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ContextBundleResponse(BaseModel):
    """Aggregated context bundle provided to an agent before execution."""

    project_id: int
    target_agent: str
    requirements: Optional[Dict[str, Any]] = None
    architecture: Optional[Dict[str, Any]] = None
    db_schema: Optional[Dict[str, Any]] = None
    api_spec: Optional[Dict[str, Any]] = None
    security_recommendations: Optional[Dict[str, Any]] = None
    qa_recommendations: Optional[Dict[str, Any]] = None
    memory_context: Optional[Dict[str, Any]] = None
    rag_context: Optional[Dict[str, Any]] = None
    assembled_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
