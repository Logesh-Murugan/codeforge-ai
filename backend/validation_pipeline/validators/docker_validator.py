"""
9. Docker Validator — Phase 5.8
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, List

from validation_pipeline.severity import IssueSeverity
from validation_pipeline.validator_result import StageResult, ValidationIssue
from validation_pipeline.validators.base_validator import BaseValidator


class DockerValidator(BaseValidator):
    def __init__(self) -> None:
        super().__init__("Docker")

    async def validate(self, project_path: str, context: Dict[str, Any]) -> StageResult:
        t0 = time.perf_counter()
        issues: List[ValidationIssue] = []

        dockerfile_p = os.path.join(project_path, "Dockerfile")
        if os.path.exists(dockerfile_p):
            with open(dockerfile_p, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if "EXPOSE" not in content:
                issues.append(
                    ValidationIssue(
                        title="Missing EXPOSE Instruction in Dockerfile",
                        description="Dockerfile does not explicitly EXPOSE container port.",
                        severity=IssueSeverity.INFO,
                        file_path="Dockerfile",
                        recommendation="Add 'EXPOSE 8000' or appropriate port in Dockerfile.",
                    )
                )

        duration_ms = (time.perf_counter() - t0) * 1000.0
        score = max(0.0, 100.0 - (len(issues) * 5.0))

        return StageResult(
            stage_name=self.stage_name,
            passed=True,
            score=score,
            execution_time_ms=duration_ms,
            issues=issues,
        )
