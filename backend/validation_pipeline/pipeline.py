"""
Validation Pipeline Executor — Phase 5.8

Sequential 12-stage automated quality gate.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List

from monitoring.events.event_bus import event_bus
from monitoring.schemas.events import MonitoringEventPayload, MonitoringEventType
from validation_pipeline.config import validation_settings
from validation_pipeline.report_generator import report_generator
from validation_pipeline.severity import IssueSeverity, PipelineStatus, QualityGrade
from validation_pipeline.validator_result import PipelineResult, StageResult, ValidationIssue
from validation_pipeline.validators import (
    ApiValidator,
    ArchitectureValidator,
    CodeQualityValidator,
    DatabaseValidator,
    DependencyValidator,
    DockerValidator,
    DocumentationValidator,
    PerformanceValidator,
    SecurityValidator,
    StructureValidator,
    SyntaxValidator,
    TestingValidator,
)

logger = logging.getLogger(__name__)


class ValidationPipeline:
    """
    12-Stage Validation Pipeline Executor.
    """

    def __init__(self) -> None:
        self.validators = [
            StructureValidator(),
            SyntaxValidator(),
            DependencyValidator(),
            ArchitectureValidator(),
            DatabaseValidator(),
            ApiValidator(),
            SecurityValidator(),
            DocumentationValidator(),
            DockerValidator(),
            TestingValidator(),
            PerformanceValidator(),
            CodeQualityValidator(),
        ]

    async def execute_pipeline(self, project_id: int, project_path: str) -> PipelineResult:
        """
        Execute 12 validation stages sequentially.
        """
        t0 = time.perf_counter()
        logger.info(f"[ValidationPipeline] Starting 12-stage validation for project #{project_id}")

        await event_bus.publish(
            MonitoringEventPayload(
                project_id=project_id,
                event_type=MonitoringEventType.VALIDATION_STARTED,
                message="Started 12-stage validation pipeline quality gate",
            )
        )

        stage_results: List[StageResult] = []
        all_issues: List[ValidationIssue] = []

        for val in self.validators:
            try:
                res = await val.validate(project_path, context={"project_id": project_id})
                stage_results.append(res)
                all_issues.extend(res.issues)
            except Exception as exc:
                logger.error(f"[ValidationPipeline] Error in stage '{val.stage_name}': {exc}")

        total_ms = (time.perf_counter() - t0) * 1000.0
        scores = [sr.score for sr in stage_results]
        overall_score = sum(scores) / len(scores) if scores else 100.0

        has_critical = any(i.severity == IssueSeverity.CRITICAL for i in all_issues)
        has_high = any(i.severity == IssueSeverity.HIGH for i in all_issues)

        if has_critical or overall_score < validation_settings.PASS_SCORE_THRESHOLD:
            status = PipelineStatus.FAILED
        elif has_high or overall_score < 85.0:
            status = PipelineStatus.WARNING
        else:
            status = PipelineStatus.PASSED

        grade = PipelineResult.calculate_grade(overall_score)

        result = PipelineResult(
            project_id=project_id,
            status=status,
            overall_score=overall_score,
            quality_grade=grade,
            total_execution_time_ms=total_ms,
            stage_results=stage_results,
            all_issues=all_issues,
        )

        await event_bus.publish(
            MonitoringEventPayload(
                project_id=project_id,
                event_type=MonitoringEventType.VALIDATION_FINISHED,
                message=f"Validation completed: {status.value} (Score: {overall_score:.1f})",
                payload={"status": status.value, "score": overall_score},
            )
        )

        return result


pipeline = ValidationPipeline()
