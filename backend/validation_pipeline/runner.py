"""
Validation Pipeline Runner — Phase 5.8
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from validation_pipeline.pipeline import pipeline
from validation_pipeline.validator_result import PipelineResult

logger = logging.getLogger(__name__)


class ValidationRunner:
    """
    Validation Pipeline Runner.
    """

    async def run(self, project_id: int, project_path: str = ".") -> PipelineResult:
        """Run validation pipeline."""
        return await pipeline.execute_pipeline(project_id, project_path)


runner = ValidationRunner()
