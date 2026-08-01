"""
Validator Results & DTOs — Phase 5.8
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from validation_pipeline.severity import IssueSeverity, PipelineStatus, QualityGrade


class ValidationIssue(BaseModel):
    title: str
    description: str
    severity: IssueSeverity = Field(default=IssueSeverity.MEDIUM)
    location: str = ""
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    recommendation: str = ""


class StageResult(BaseModel):
    stage_name: str
    passed: bool = True
    score: float = Field(default=100.0, ge=0.0, le=100.0)
    execution_time_ms: float = Field(default=0.0)
    issues: List[ValidationIssue] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)


class PipelineResult(BaseModel):
    project_id: int
    status: PipelineStatus = Field(default=PipelineStatus.PASSED)
    overall_score: float = Field(default=100.0, ge=0.0, le=100.0)
    quality_grade: QualityGrade = Field(default=QualityGrade.A_PLUS)
    total_execution_time_ms: float = Field(default=0.0)
    stage_results: List[StageResult] = Field(default_factory=list)
    all_issues: List[ValidationIssue] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def calculate_grade(cls, score: float) -> QualityGrade:
        if score >= 95.0:
            return QualityGrade.A_PLUS
        elif score >= 90.0:
            return QualityGrade.A
        elif score >= 80.0:
            return QualityGrade.B
        elif score >= 70.0:
            return QualityGrade.C
        elif score >= 60.0:
            return QualityGrade.D
        else:
            return QualityGrade.F
