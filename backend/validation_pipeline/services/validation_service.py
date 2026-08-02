"""
Validation Service — Phase 5.8
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from validation_pipeline.pipeline import pipeline
from validation_pipeline.services.report_builder import report_builder
from validation_pipeline.services.scoring_engine import scoring_engine
from validation_pipeline.validator_result import PipelineResult

logger = logging.getLogger(__name__)


class ValidationService:
    """
    Validation Service Facade.
    """

    async def run_validation(self, project_id: int, project_path: str) -> PipelineResult:
        """Execute validation pipeline for project_id."""
        return await pipeline.execute_pipeline(project_id, project_path)

    async def get_validation_result(self, project_id: int) -> Dict[str, Any]:
        """Get validation result."""
        res = await pipeline.execute_pipeline(project_id, f"generated_projects/project_{project_id}")
        data = res.model_dump()
        data["quality_label"] = scoring_engine.get_quality_grade_label(res.overall_score)
        return data


validation_service = ValidationService()
