"""
3. Dependency Validator — Phase 5.8
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, List

from validation_pipeline.severity import IssueSeverity
from validation_pipeline.validator_result import StageResult, ValidationIssue
from validation_pipeline.validators.base_validator import BaseValidator


class DependencyValidator(BaseValidator):
    def __init__(self) -> None:
        super().__init__("Dependencies")

    async def validate(self, project_path: str, context: Dict[str, Any]) -> StageResult:
        t0 = time.perf_counter()
        issues: List[ValidationIssue] = []

        req_p = os.path.join(project_path, "requirements.txt")
        if os.path.exists(req_p):
            with open(req_p, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            pkg_names = [l.strip().split("==")[0].split(">=")[0] for l in lines if l.strip() and not l.startswith("#")]
            if len(pkg_names) != len(set(pkg_names)):
                issues.append(
                    ValidationIssue(
                        title="Duplicate Dependencies in requirements.txt",
                        description="requirements.txt contains duplicate package declarations.",
                        severity=IssueSeverity.LOW,
                        file_path="requirements.txt",
                        recommendation="Deduplicate requirements.txt dependency list.",
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
