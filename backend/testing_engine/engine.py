"""
TestingEngine — Phase 4.4

Runs all 15 automated checks and produces a TestingReport.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from testing_engine.schemas import TestingReport, TestingRequest, TestResult
from testing_engine.tests import TEST_REGISTRY

logger = logging.getLogger(__name__)


class TestingEngine:
    """
    Runs the self-test pipeline against a generated project.

    Pipeline stages (map to TEST_REGISTRY keys):
        Compilation (T01–T03) → Startup (T04, T07, T10) →
        Database (T05) → Security (T06, T08, T09) →
        Documentation (T12) → Docker (T11, T14) →
        Export (T13) → Packaging (T15)
    """

    def run(
        self,
        project_id: int,
        project_title: str,
        generated_files: List[Dict[str, str]],
        agent_outputs: Optional[Dict[str, Any]] = None,
        test_ids: Optional[List[str]] = None,
    ) -> TestingReport:
        """
        Execute all (or selected) tests.

        Args:
            project_id:       DB project ID.
            project_title:    Display name.
            generated_files:  List of {path, content} dicts.
            agent_outputs:    Map of agent_name → output_json.
            test_ids:         Specific test IDs to run (T01–T15). None = all.

        Returns:
            :class:`TestingReport`
        """
        files_dict: Dict[str, str] = {
            f.get("path", f"file_{i}"): f.get("content", "")
            for i, f in enumerate(generated_files)
        }
        ao = agent_outputs or {}
        enabled_ids = test_ids or list(TEST_REGISTRY.keys())

        results: List[TestResult] = []
        for tid in enabled_ids:
            fn = TEST_REGISTRY.get(tid)
            if not fn:
                logger.warning("[TESTING] Unknown test ID: %s", tid)
                continue
            try:
                result = fn(files=files_dict, agent_outputs=ao)
                results.append(result)
                logger.debug("[TESTING] %s (%s) → %s", tid, result.name, result.status)
            except Exception as exc:
                logger.error("[TESTING] Test %s crashed: %s", tid, exc)
                from testing_engine.schemas import TestStatus
                results.append(TestResult(
                    test_id=tid,
                    name=f"Test {tid}",
                    category="unknown",
                    status=TestStatus.FAIL,
                    message=f"Test runner error: {exc}",
                ))

        report = TestingReport.compute(project_id, project_title, results)
        logger.info(
            "[TESTING] Project %d: %s score=%d pass=%d fail=%d",
            project_id, report.overall_status, report.score,
            report.passed, report.failed,
        )
        return report
