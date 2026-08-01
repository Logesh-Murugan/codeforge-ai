"""
11. Performance Validator — Phase 5.8
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, List

from validation_pipeline.severity import IssueSeverity
from validation_pipeline.validator_result import StageResult, ValidationIssue
from validation_pipeline.validators.base_validator import BaseValidator


class PerformanceValidator(BaseValidator):
    def __init__(self) -> None:
        super().__init__("Performance")

    async def validate(self, project_path: str, context: Dict[str, Any]) -> StageResult:
        t0 = time.perf_counter()
        issues: List[ValidationIssue] = []

        if os.path.exists(project_path):
            for root, _, files in os.walk(project_path):
                for file in files:
                    if file.endswith(".py"):
                        file_p = os.path.join(root, file)
                        rel_p = os.path.relpath(file_p, project_path)
                        with open(file_p, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        if "time.sleep(" in content and "async def" in content:
                            issues.append(
                                ValidationIssue(
                                    title=f"Blocking time.sleep() inside async function in {file}",
                                    description="Blocking synchronous sleep inside coroutine blocks the event loop.",
                                    severity=IssueSeverity.MEDIUM,
                                    file_path=rel_p,
                                    recommendation="Use asyncio.sleep() instead of time.sleep().",
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
