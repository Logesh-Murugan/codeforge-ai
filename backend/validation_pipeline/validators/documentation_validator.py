"""
8. Documentation Validator — Phase 5.8
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, List

from validation_pipeline.severity import IssueSeverity
from validation_pipeline.validator_result import StageResult, ValidationIssue
from validation_pipeline.validators.base_validator import BaseValidator


class DocumentationValidator(BaseValidator):
    def __init__(self) -> None:
        super().__init__("Documentation")

    async def validate(self, project_path: str, context: Dict[str, Any]) -> StageResult:
        t0 = time.perf_counter()
        issues: List[ValidationIssue] = []

        readme_p = os.path.join(project_path, "README.md")
        if os.path.exists(readme_p):
            with open(readme_p, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if len(content.strip()) < 100:
                issues.append(
                    ValidationIssue(
                        title="Insufficient README Documentation",
                        description="README.md is overly brief (<100 chars).",
                        severity=IssueSeverity.LOW,
                        file_path="README.md",
                        recommendation="Expand README to include Installation, Configuration, and API documentation sections.",
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
