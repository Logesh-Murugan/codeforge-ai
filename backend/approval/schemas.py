"""
Approval Schemas — Phase 5.3

Pydantic models for human-in-the-loop approval workflows.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DecisionType(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    REGENERATE = "regenerate"
    EDIT = "edit"
    CONTINUE = "continue"


class ApprovalDecisionRequest(BaseModel):
    """Request payload to submit a human decision on a pending step."""

    project_id: int = Field(..., description="Owning project ID.")
    decision: DecisionType = Field(
        ...,
        description="Decision action: approve, reject, regenerate, edit, or continue.",
    )
    agent_name: Optional[str] = Field(
        default=None,
        description="Name of the agent step being acted upon.",
    )
    edited_output: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Overridden/edited output dictionary (required for decision='edit').",
    )
    feedback: Optional[str] = Field(
        default=None,
        description="Optional human feedback or review notes.",
    )


class ApprovalDecisionResponse(BaseModel):
    """Response payload after processing a decision."""

    project_id: int
    decision: str
    agent_name: str
    status: str = Field(..., description="Updated pipeline / step status.")
    message: str
    current_agent: Optional[str] = None
    next_agent: Optional[str] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PendingApprovalItem(BaseModel):
    """Details of an active item waiting for human approval."""

    project_id: int
    agent_name: str
    agent_run_id: Optional[int] = None
    status: str = "pending"
    output: Optional[Dict[str, Any]] = None
    next_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ApprovalConfigRequest(BaseModel):
    """Request payload to configure approval mode for a project."""

    project_id: int
    approval_mode: bool = Field(
        ...,
        description="Enable (True) or disable (False) human approval requirement.",
    )


class ApprovalConfigResponse(BaseModel):
    """Response payload for approval configuration update."""

    project_id: int
    approval_mode: bool
    message: str


class ApprovalHistoryItem(BaseModel):
    """Audit entry recording a human approval decision."""

    project_id: int
    agent_name: str
    decision: str
    feedback: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
