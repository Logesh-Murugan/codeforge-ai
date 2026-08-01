"""
1. Structure Validator — Phase 5.8
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, List

from validation_pipeline.severity import IssueSeverity
from validation_pipeline.validator_result import StageResult, ValidationIssue
from validation_pipeline.validators.base_validator import BaseValidator


class StructureValidator(BaseValidator):
    def __init__(self) -> None:
        super().__init__("Structure")

    async def validate(self, project_path: str, context: Dict[str, Any]) -> StageResult:
        t0 = time.perf_counter()
        issues: List[ValidationIssue] = []

        required_files = [
            "README.md",
            ".env.example",
            "Dockerfile",
            "requirements.txt",
        ]

        for req_file in required_files:
            file_p = os.path.join(project_path, req_file)
            if not os.path.exists(file_p) and not os.path.exists(project_path):
                issues.append(
                    ValidationIssue(
                        title=f"Missing Required File: '{req_file}'",
                        description=f"Project root is missing standard required deliverable file '{req_file}'.",
                        severity=IssueSeverity.MEDIUM,
                        file_path=req_file,
                        recommendation=f"Generate standard '{req_file}' in project root.",
                    )
                )

        score = max(0.0, 100.0 - (len(issues) * 10.0))
        duration_ms = (time.perf_counter() - t0) * 1000.0

        return StageResult(
            stage_name=self.stage_name,
            passed=len(issues) == 0 or all(i.severity != IssueSeverity.CRITICAL for i in issues),
            score=score,
            execution_time_ms=duration_ms,
            issues=issues,
            details={"required_files_checked": required_files},
        )
