"""
10. Testing Validator — Phase 5.8
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, List

from validation_pipeline.severity import IssueSeverity
from validation_pipeline.validator_result import StageResult, ValidationIssue
from validation_pipeline.validators.base_validator import BaseValidator


class TestingValidator(BaseValidator):
    def __init__(self) -> None:
        super().__init__("Testing")

    async def validate(self, project_path: str, context: Dict[str, Any]) -> StageResult:
        t0 = time.perf_counter()
        issues: List[ValidationIssue] = []

        tests_dir = os.path.join(project_path, "tests")
        if not os.path.exists(tests_dir) and os.path.exists(project_path):
            issues.append(
                ValidationIssue(
                    title="Missing Tests Directory",
                    description="Project is missing automated tests directory.",
                    severity=IssueSeverity.LOW,
                    file_path="tests",
                    recommendation="Add unit and integration tests.",
                )
            )

        duration_ms = (time.perf_counter() - t0) * 1000.0
        score = max(0.0, 100.0 - (len(issues) * 10.0))

        return StageResult(
            stage_name=self.stage_name,
            passed=True,
            score=score,
            execution_time_ms=duration_ms,
            issues=issues,
        )
