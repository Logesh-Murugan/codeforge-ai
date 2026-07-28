"""
ValidationEngine — Phase 4.2

Orchestrates all validators and produces a final ValidationReport.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from validation_engine.schemas import (
    CategoryResult,
    ProjectFiles,
    ValidationReport,
    ValidationRequest,
    ValidationStatus,
)
from validation_engine.validators import VALIDATOR_REGISTRY

logger = logging.getLogger(__name__)


class ValidationEngine:
    """
    Runs all category validators against a generated project and returns
    a :class:`ValidationReport`.

    Args:
        memory_service: Optional injected MemoryService (unused currently
                        but reserved for future cross-referencing).
    """

    def __init__(self, memory_service=None) -> None:
        self._memory = memory_service

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate(
        self,
        project_files: ProjectFiles,
        project_id: int,
        project_title: str,
        categories: Optional[List[str]] = None,
    ) -> ValidationReport:
        """
        Run all (or selected) validators.

        Args:
            project_files: File contents and agent outputs.
            project_id:    DB project ID.
            project_title: Display name.
            categories:    Subset of VALIDATOR_REGISTRY keys. None = all.

        Returns:
            :class:`ValidationReport`
        """
        enabled = categories or list(VALIDATOR_REGISTRY.keys())
        results: List[CategoryResult] = []

        for cat in enabled:
            validator_fn = VALIDATOR_REGISTRY.get(cat)
            if not validator_fn:
                logger.warning("[VALIDATION] Unknown category: %s", cat)
                continue
            try:
                result = validator_fn(project_files)
                results.append(result)
                logger.debug(
                    "[VALIDATION] %s → %s (score=%d, errors=%d)",
                    cat, result.status, result.score, result.error_count,
                )
            except Exception as exc:
                logger.error("[VALIDATION] Validator '%s' crashed: %s", cat, exc)
                results.append(CategoryResult(
                    category=cat,
                    status=ValidationStatus.FAIL,
                    score=0,
                    checks_run=1,
                    checks_passed=0,
                ))

        report = ValidationReport.compute(project_id, project_title, results)
        logger.info(
            "[VALIDATION] Project %d: %s score=%d errors=%d",
            project_id, report.overall_status, report.production_readiness_score,
            report.total_errors,
        )
        return report

    def validate_from_bundle(
        self,
        project_id: int,
        project_title: str,
        generated_files: List[Dict[str, str]],
        agent_outputs: Dict[str, Any],
        categories: Optional[List[str]] = None,
    ) -> ValidationReport:
        """
        Convenience method: build ProjectFiles from raw data then validate.

        Args:
            project_id:       DB project ID.
            project_title:    Display name.
            generated_files:  List of {path, content} dicts.
            agent_outputs:    Map of agent_name → output_json.
            categories:       Validators to run. None = all.
        """
        files_dict: Dict[str, str] = {
            f.get("path", f"file_{i}"): f.get("content", "")
            for i, f in enumerate(generated_files)
        }
        project_files = ProjectFiles(
            files=files_dict,
            agent_outputs=agent_outputs,
            project_metadata={"project_id": project_id, "title": project_title},
        )
        return self.validate(project_files, project_id, project_title, categories)
