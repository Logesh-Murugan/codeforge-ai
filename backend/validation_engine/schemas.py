"""
Validation Engine Pydantic schemas — Phase 4.2
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ValidationSeverity(str, Enum):
    ERROR       = "error"
    WARNING     = "warning"
    INFO        = "info"


class ValidationStatus(str, Enum):
    PASS    = "pass"
    FAIL    = "fail"
    SKIPPED = "skipped"


class ValidationIssue(BaseModel):
    """A single validation finding."""
    category: str
    severity: ValidationSeverity
    code: str            # short machine-readable code, e.g. "MISSING_ROUTER"
    message: str
    file: Optional[str] = None
    line: Optional[int] = None
    recommendation: Optional[str] = None


class CategoryResult(BaseModel):
    """Result for one validation category."""
    category: str
    status: ValidationStatus
    score: int = Field(ge=0, le=100, description="0–100 category score")
    issues: List[ValidationIssue] = Field(default_factory=list)
    checks_run: int = 0
    checks_passed: int = 0

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.WARNING)


class ValidationReport(BaseModel):
    """Complete validation report for a generated project."""
    project_id: int
    project_title: str
    overall_status: ValidationStatus
    production_readiness_score: int = Field(ge=0, le=100)
    categories: List[CategoryResult] = Field(default_factory=list)
    total_errors: int = 0
    total_warnings: int = 0
    total_recommendations: int = 0
    summary: str = ""
    validated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @classmethod
    def compute(
        cls,
        project_id: int,
        project_title: str,
        categories: List[CategoryResult],
    ) -> "ValidationReport":
        """Build a ValidationReport from category results."""
        total_errors   = sum(c.error_count for c in categories)
        total_warnings = sum(c.warning_count for c in categories)
        total_recs     = sum(
            sum(1 for i in c.issues if i.recommendation)
            for c in categories
        )
        # Weighted average score
        score = int(sum(c.score for c in categories) / len(categories)) if categories else 0
        overall = ValidationStatus.PASS if total_errors == 0 else ValidationStatus.FAIL

        icon = "✅" if overall == ValidationStatus.PASS else "❌"
        summary = (
            f"{icon} {overall.value.upper()} — "
            f"Score: {score}/100 · "
            f"Errors: {total_errors} · Warnings: {total_warnings}"
        )

        return cls(
            project_id=project_id,
            project_title=project_title,
            overall_status=overall,
            production_readiness_score=score,
            categories=categories,
            total_errors=total_errors,
            total_warnings=total_warnings,
            total_recommendations=total_recs,
            summary=summary,
        )


class ValidationRequest(BaseModel):
    """Request body to trigger validation."""
    project_id: int
    categories: Optional[List[str]] = None   # None = all


class ProjectFiles(BaseModel):
    """File-based representation of a generated project for static analysis."""
    files: Dict[str, str] = Field(default_factory=dict)  # path → content
    agent_outputs: Dict[str, Any] = Field(default_factory=dict)
    project_metadata: Dict[str, Any] = Field(default_factory=dict)

    def get(self, path: str) -> Optional[str]:
        return self.files.get(path)

    def find(self, pattern: str) -> List[str]:
        """Return all file paths containing *pattern* (case-insensitive substring)."""
        pat = pattern.lower()
        return [p for p in self.files if pat in p.lower()]

    def content_of(self, path: str) -> str:
        return self.files.get(path, "")
