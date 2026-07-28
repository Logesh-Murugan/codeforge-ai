"""
ReportService — Phase 4.1

Orchestrates individual report exporters and returns a list of GeneratedReports.
"""
from __future__ import annotations

import logging
from typing import List

from export_engine.exporters.report_exporters import EXPORTER_REGISTRY
from export_engine.schemas import GeneratedReport, ProjectBundle, ReportType

logger = logging.getLogger(__name__)


class ReportService:
    """
    Runs each enabled exporter against a ProjectBundle and collects results.
    """

    def generate(
        self,
        bundle: ProjectBundle,
        report_types: List[ReportType] | None = None,
    ) -> List[GeneratedReport]:
        """
        Generate all requested reports.

        Args:
            bundle:       Full project data bundle.
            report_types: Which reports to produce. ``None`` → all.

        Returns:
            List of :class:`GeneratedReport` objects.
        """
        if report_types is None:
            report_types = [rt for rt in ReportType if rt != ReportType.FULL_PROJECT]

        reports: List[GeneratedReport] = []
        for rt in report_types:
            exporter = EXPORTER_REGISTRY.get(rt)
            if not exporter:
                logger.warning("[REPORT] No exporter registered for %s", rt)
                continue
            try:
                report = exporter(bundle)
                reports.append(report)
                logger.debug("[REPORT] Generated %s (%d chars)", rt, len(report.content))
            except Exception as exc:
                logger.error("[REPORT] Failed to generate %s: %s", rt, exc)

        logger.info("[REPORT] Generated %d/%d reports for project %d",
                    len(reports), len(report_types), bundle.metadata.project_id)
        return reports
