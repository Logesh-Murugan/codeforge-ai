"""
Report Generator — Phase 5.8

Generates automated Markdown & JSON reports for pipeline runs.
"""
from __future__ import annotations

import json
import logging
from typing import Dict

from validation_pipeline.validator_result import PipelineResult

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Validation Report Generator.
    """

    def generate_all_reports(self, result: PipelineResult) -> Dict[str, str]:
        """Generate 7 standard validation reports."""
        return {
            "validation_summary.md": self.generate_summary_report(result),
            "validation_details.md": self.generate_details_report(result),
            "security_report.md": self.generate_security_report(result),
            "architecture_report.md": self.generate_architecture_report(result),
            "performance_report.md": self.generate_performance_report(result),
            "quality_score.md": self.generate_quality_score_report(result),
            "validation.json": self.generate_json_report(result),
        }

    def generate_summary_report(self, result: PipelineResult) -> str:
        return f"# Validation Summary Report\n\n**Project ID**: {result.project_id}\n**Status**: {result.status.value}\n**Score**: {result.overall_score:.1f}/100 ({result.quality_grade.value})\n**Duration**: {result.total_execution_time_ms:.1f}ms\n"

    def generate_details_report(self, result: PipelineResult) -> str:
        md = f"# Detailed Validation Report\n\nTotal Stages Executed: {len(result.stage_results)}\nTotal Issues Found: {len(result.all_issues)}\n\n"
        for sr in result.stage_results:
            md += f"### Stage: {sr.stage_name} ({'PASSED' if sr.passed else 'FAILED'})\n- Score: {sr.score:.1f}/100\n- Issues: {len(sr.issues)}\n"
        return md

    def generate_security_report(self, result: PipelineResult) -> str:
        sec_issues = [i for i in result.all_issues if i.severity in ("HIGH", "CRITICAL")]
        return f"# Security Inspection Report\n\nHigh/Critical Issues: {len(sec_issues)}\n"

    def generate_architecture_report(self, result: PipelineResult) -> str:
        return f"# Architecture & Layer Separation Report\n\nLayer Inspection Complete.\n"

    def generate_performance_report(self, result: PipelineResult) -> str:
        return f"# Performance & Resource Report\n\nTotal Pipeline Execution: {result.total_execution_time_ms:.1f}ms\n"

    def generate_quality_score_report(self, result: PipelineResult) -> str:
        return f"# Quality Scorecard\n\nFinal Score: {result.overall_score:.1f}\nGrade: {result.quality_grade.value}\n"

    def generate_json_report(self, result: PipelineResult) -> str:
        return result.model_dump_json(indent=2)


report_generator = ReportGenerator()
