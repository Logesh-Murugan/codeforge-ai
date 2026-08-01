"""
4. Architecture Validator — Phase 5.8
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, List

from validation_pipeline.severity import IssueSeverity
from validation_pipeline.validator_result import StageResult, ValidationIssue
from validation_pipeline.validators.base_validator import BaseValidator


class ArchitectureValidator(BaseValidator):
    def __init__(self) -> None:
        super().__init__("Architecture")

    async def validate(self, project_path: str, context: Dict[str, Any]) -> StageResult:
        t0 = time.perf_counter()
        issues: List[ValidationIssue] = []

        if os.path.exists(project_path):
            for root, _, files in os.walk(project_path):
                for file in files:
                    if file.endswith(".py") or file.endswith(".ts") or file.endswith(".tsx"):
                        file_p = os.path.join(root, file)
                        rel_p = os.path.relpath(file_p, project_path)
                        with open(file_p, "r", encoding="utf-8", errors="ignore") as f:
                            line_count = len(f.readlines())
                        if line_count > 1000:
                            issues.append(
                                ValidationIssue(
                                    title=f"Large File Detected: {file} ({line_count} lines)",
                                    description=f"File exceeds 1000 lines threshold, indicating potential God Class violation.",
                                    severity=IssueSeverity.MEDIUM,
                                    file_path=rel_p,
                                    recommendation="Refactor file into modular decoupled components.",
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
