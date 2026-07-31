"""
Validation Schemas — Phase 5.4

Pydantic data models for cross-agent validation and feedback loops.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CrossValidationRequest(BaseModel):
    """Request to validate output between two agents (e.g., Security -> Backend)."""

    project_id: int
    validator_agent: str = Field(..., description="Agent conducting the review.")
    target_agent: str = Field(..., description="Agent whose output is being reviewed.")
    target_output: Dict[str, Any] = Field(..., description="Output payload being evaluated.")


class ValidationRuleResult(BaseModel):
    rule_name: str
    passed: bool
    score: float = 1.0
    details: Optional[str] = None


class CrossValidationResponse(BaseModel):
    """Result of a cross-agent validation check."""

    project_id: int
    validator_agent: str
    target_agent: str
    is_valid: bool
    agreement_score: float = Field(..., ge=0.0, le=1.0)
    rule_results: List[ValidationRuleResult] = Field(default_factory=list)
    feedback: Optional[str] = None
    validated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FeedbackRequest(BaseModel):
    """Payload to record cross-agent feedback."""

    project_id: int
    from_agent: str
    to_agent: str
    feedback_type: str = Field(default="correction", description="correction, enhancement, or warning")
    comments: str
    suggested_changes: Optional[Dict[str, Any]] = None


class FeedbackResponse(BaseModel):
    """Response payload for recorded feedback."""

    feedback_id: int
    project_id: int
    from_agent: str
    to_agent: str
    status: str = "open"  # open, resolved, ignored
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UpdateFeedbackRequest(BaseModel):
    """Request payload to update feedback status (PUT)."""

    status: str = Field(..., description="open, resolved, ignored")
    resolution_notes: Optional[str] = None
