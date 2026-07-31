"""
Context Validation Schemas — Phase 5.5

Schemas for validating missing, invalid, duplicate, conflicting, empty, expired, or corrupted contexts.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ContextValidationErrorType(str, Enum):
    MISSING = "missing"
    INVALID = "invalid"
    DUPLICATE = "duplicate"
    CONFLICTING = "conflicting"
    EMPTY = "empty"
    EXPIRED = "expired"
    CORRUPTED = "corrupted"


class ContextValidationIssue(BaseModel):
    context_type: str
    error_type: ContextValidationErrorType
    description: str
    severity: str = "warning"  # warning, error, critical


class ContextValidationResponse(BaseModel):
    """Result of context validation pipeline."""

    project_id: int
    target_agent: Optional[str] = None
    is_valid: bool
    total_issues: int
    issues: List[ContextValidationIssue] = Field(default_factory=list)
    validated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
