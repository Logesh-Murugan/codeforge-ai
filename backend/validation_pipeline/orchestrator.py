"""
Orchestrator Integration Hook — Phase 5.8
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from validation_pipeline.pipeline import pipeline
from validation_pipeline.validator_result import PipelineResult

logger = logging.getLogger(__name__)


async def run_post_generation_validation(project_id: int, project_path: str) -> PipelineResult:
    """
    Hook called after DevOps Engineer agent completes code generation.
    """
    logger.info(f"[OrchestratorHook] Triggering post-generation validation quality gate for project #{project_id}")
    return await pipeline.execute_pipeline(project_id, project_path)
