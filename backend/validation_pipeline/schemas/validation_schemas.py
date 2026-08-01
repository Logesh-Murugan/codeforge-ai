"""
Validation Pipeline Pydantic Schemas — Phase 5.8
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from validation_pipeline.severity import IssueSeverity, PipelineStatus, QualityGrade


class IssueDTO(BaseModel):
    title: str
    description: str
    severity: IssueSeverity
    location: str = ""
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    recommendation: str = ""


class StageResultDTO(BaseModel):
    stage_name: str
    passed: bool
    score: float
    execution_time_ms: float
    issues: List[IssueDTO] = Field(default_factory=list)


class ValidationRunDTO(BaseModel):
    run_id: int
    project_id: int
    status: PipelineStatus
    score: float
    quality_grade: QualityGrade
    duration_ms: float
    executed_at: datetime
    stage_results: List[StageResultDTO] = Field(default_factory=list)
    issues: List[IssueDTO] = Field(default_factory=list)


class RunValidationRequest(BaseModel):
    project_id: int = Field(default=1)
    project_path: Optional[str] = None
