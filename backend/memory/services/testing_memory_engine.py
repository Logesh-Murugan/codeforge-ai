"""
TestingMemoryEngine — Phase 5.1

Domain-specific memory engine for test results, coverage reports,
test suites, and quality metrics.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from memory.persistent_schemas import MemoryCategory, PersistentMemoryResponse
from memory.services.base_memory_service import BaseMemoryEngine

logger = logging.getLogger(__name__)


class TestingMemoryEngine(BaseMemoryEngine):
    """Engine for testing memory entries."""

    CATEGORY = MemoryCategory.TESTING
    DOMAIN_FIELDS = [
        "test_type", "coverage_percent", "pass_rate",
        "test_suite", "test_framework", "total_tests",
        "failed_tests", "skipped_tests",
    ]

    async def get_by_test_type(
        self,
        project_id: int,
        test_type: str,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryResponse]:
        """Retrieve entries filtered by test type (unit/integration/e2e)."""
        entries = await self.list_entries(project_id=project_id, session=session)
        return [
            e for e in entries
            if e.metadata_json.get("test_type") == test_type
        ]

    async def get_by_suite(
        self,
        project_id: int,
        test_suite: str,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryResponse]:
        """Retrieve entries for a specific test suite."""
        entries = await self.list_entries(project_id=project_id, session=session)
        return [
            e for e in entries
            if e.metadata_json.get("test_suite") == test_suite
        ]

    async def get_quality_report(
        self,
        project_id: int,
        session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Build a quality report with aggregated test metrics."""
        entries = await self.list_entries(
            project_id=project_id, limit=500, session=session,
        )
        by_type: Dict[str, int] = {}
        total_tests_sum = 0
        failed_tests_sum = 0
        skipped_tests_sum = 0
        coverage_values: List[float] = []
        pass_rate_values: List[float] = []

        for e in entries:
            meta = e.metadata_json
            tt = meta.get("test_type", "unknown")
            by_type[tt] = by_type.get(tt, 0) + 1
            total_tests_sum += meta.get("total_tests", 0) or 0
            failed_tests_sum += meta.get("failed_tests", 0) or 0
            skipped_tests_sum += meta.get("skipped_tests", 0) or 0
            cov = meta.get("coverage_percent")
            if cov is not None:
                coverage_values.append(float(cov))
            pr = meta.get("pass_rate")
            if pr is not None:
                pass_rate_values.append(float(pr))

        avg_coverage = (
            sum(coverage_values) / len(coverage_values)
            if coverage_values else None
        )
        avg_pass_rate = (
            sum(pass_rate_values) / len(pass_rate_values)
            if pass_rate_values else None
        )

        return {
            "total_entries": len(entries),
            "by_test_type": by_type,
            "total_tests": total_tests_sum,
            "failed_tests": failed_tests_sum,
            "skipped_tests": skipped_tests_sum,
            "avg_coverage_percent": round(avg_coverage, 2) if avg_coverage is not None else None,
            "avg_pass_rate": round(avg_pass_rate, 2) if avg_pass_rate is not None else None,
        }
