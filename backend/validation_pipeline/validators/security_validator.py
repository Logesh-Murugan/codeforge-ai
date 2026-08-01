"""
7. Security Validator — Phase 5.8
"""
from __future__ import annotations

import os
import re
import time
from typing import Any, Dict, List

from validation_pipeline.severity import IssueSeverity
from validation_pipeline.validator_result import StageResult, ValidationIssue
from validation_pipeline.validators.base_validator import BaseValidator


class SecurityValidator(BaseValidator):
    def __init__(self) -> None:
        super().__init__("Security")

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
                            content = f.read()

                        if "eval(" in content:
                            issues.append(
                                ValidationIssue(
                                    title=f"Unsafe eval() usage in {file}",
                                    description="Usage of built-in eval() introduces dynamic code injection vulnerabilities.",
                                    severity=IssueSeverity.HIGH,
                                    file_path=rel_p,
                                    recommendation="Replace eval() with safe parsing utilities.",
                                )
                            )

                        if re.search(r"secret_key\s*=\s*['\"][A-Za-z0-9_-]{10,}['\"]", content, re.IGNORECASE):
                            issues.append(
                                ValidationIssue(
                                    title=f"Hardcoded Secret Key in {file}",
                                    description="Hardcoded secret key string detected in source code.",
                                    severity=IssueSeverity.HIGH,
                                    file_path=rel_p,
                                    recommendation="Load secret key from environment variables via config.",
                                )
                            )

        duration_ms = (time.perf_counter() - t0) * 1000.0
        score = max(0.0, 100.0 - (len(issues) * 15.0))

        return StageResult(
            stage_name=self.stage_name,
            passed=all(i.severity != IssueSeverity.CRITICAL for i in issues),
            score=score,
            execution_time_ms=duration_ms,
            issues=issues,
        )
