"""
Context Scoring Schemas — Phase 5.5

Schemas for 6-tier quality score metrics (Relevancy, Confidence, Priority, Freshness, Source, Overall Quality).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Optional
from pydantic import BaseModel, Field


class ContextQualityScoreResponse(BaseModel):
    """6-tier quality score for a context item or project context set."""

    project_id: int
    context_type: Optional[str] = None
    relevancy_score: float = Field(..., ge=0.0, le=1.0)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    priority_score: float = Field(..., ge=0.0, le=1.0)
    freshness_score: float = Field(..., ge=0.0, le=1.0)
    source_score: float = Field(..., ge=0.0, le=1.0)
    overall_quality_score: float = Field(..., ge=0.0, le=1.0)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
