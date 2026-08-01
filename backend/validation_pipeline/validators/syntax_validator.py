"""
2. Syntax Validator — Phase 5.8
"""
from __future__ import annotations

import ast
import json
import os
import time
from typing import Any, Dict, List

from validation_pipeline.severity import IssueSeverity
from validation_pipeline.validator_result import StageResult, ValidationIssue
from validation_pipeline.validators.base_validator import BaseValidator


class SyntaxValidator(BaseValidator):
    def __init__(self) -> None:
        super().__init__("Syntax")

    async def validate(self, project_path: str, context: Dict[str, Any]) -> StageResult:
        t0 = time.perf_counter()
        issues: List[ValidationIssue] = []

        if os.path.exists(project_path):
            for root, _, files in os.walk(project_path):
                for file in files:
                    file_p = os.path.join(root, file)
                    rel_p = os.path.relpath(file_p, project_path)

                    if file.endswith(".py"):
                        try:
                            with open(file_p, "r", encoding="utf-8", errors="ignore") as f:
                                code = f.read()
                            ast.parse(code, filename=file_p)
                        except SyntaxError as exc:
                            issues.append(
                                ValidationIssue(
                                    title=f"Python Syntax Error in {file}",
                                    description=str(exc),
                                    severity=IssueSeverity.CRITICAL,
                                    file_path=rel_p,
                                    line_number=exc.lineno,
                                    recommendation="Fix Python syntax error before exporting.",
                                )
                            )
                    elif file.endswith(".json"):
                        try:
                            with open(file_p, "r", encoding="utf-8", errors="ignore") as f:
                                json.load(f)
                        except json.JSONDecodeError as exc:
                            issues.append(
                                ValidationIssue(
                                    title=f"JSON Syntax Error in {file}",
                                    description=str(exc),
                                    severity=IssueSeverity.HIGH,
                                    file_path=rel_p,
                                    line_number=exc.lineno,
                                    recommendation="Fix JSON formatting syntax.",
                                )
                            )

        score = max(0.0, 100.0 - (len(issues) * 20.0))
        duration_ms = (time.perf_counter() - t0) * 1000.0

        return StageResult(
            stage_name=self.stage_name,
            passed=all(i.severity != IssueSeverity.CRITICAL for i in issues),
            score=score,
            execution_time_ms=duration_ms,
            issues=issues,
        )
