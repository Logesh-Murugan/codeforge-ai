"""
Testing Engine Pydantic schemas — Phase 4.4
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TestStatus(str, Enum):
    PASS    = "pass"
    FAIL    = "fail"
    WARN    = "warn"
    SKIPPED = "skipped"


class TestResult(BaseModel):
    """Result of a single automated test check."""
    test_id: str
    name: str
    category: str
    status: TestStatus
    message: str
    details: Optional[str] = None
    recommendations: List[str] = Field(default_factory=list)
    duration_ms: float = 0.0


class TestingReport(BaseModel):
    """Full self-test report for a generated project."""
    project_id: int
    project_title: str
    overall_status: TestStatus
    production_ready: bool
    score: int = Field(ge=0, le=100)
    results: List[TestResult] = Field(default_factory=list)
    passed: int = 0
    failed: int = 0
    warned: int = 0
    skipped: int = 0
    total_recommendations: int = 0
    summary: str = ""
    tested_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @classmethod
    def compute(
        cls,
        project_id: int,
        project_title: str,
        results: List[TestResult],
    ) -> "TestingReport":
        passed  = sum(1 for r in results if r.status == TestStatus.PASS)
        failed  = sum(1 for r in results if r.status == TestStatus.FAIL)
        warned  = sum(1 for r in results if r.status == TestStatus.WARN)
        skipped = sum(1 for r in results if r.status == TestStatus.SKIPPED)
        total   = len(results)
        recs    = sum(len(r.recommendations) for r in results)

        score = int((passed / total) * 100) if total else 100
        overall = TestStatus.PASS if failed == 0 else TestStatus.FAIL
        prod_ready = failed == 0

        icon = "✅" if overall == TestStatus.PASS else "❌"
        summary = (
            f"{icon} {overall.value.upper()} — "
            f"Score: {score}/100 · "
            f"Pass: {passed} · Fail: {failed} · Warn: {warned} · Skip: {skipped}"
        )

        return cls(
            project_id=project_id,
            project_title=project_title,
            overall_status=overall,
            production_ready=prod_ready,
            score=score,
            results=results,
            passed=passed,
            failed=failed,
            warned=warned,
            skipped=skipped,
            total_recommendations=recs,
            summary=summary,
        )


class TestingRequest(BaseModel):
    """Request body to trigger self-testing."""
    project_id: int
    test_ids: Optional[List[str]] = None   # None = all 15 tests
