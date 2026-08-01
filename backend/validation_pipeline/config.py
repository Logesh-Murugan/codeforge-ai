"""
Validation Pipeline Configuration — Phase 5.8
"""
from __future__ import annotations

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class ValidationPipelineSettings(BaseSettings):
    """
    Settings for Validation Pipeline System.
    """

    PASS_SCORE_THRESHOLD: float = Field(
        default=70.0,
        description="Minimum score (0-100) required to pass validation.",
    )

    CRITICAL_ISSUES_FAIL_IMMEDIATELY: bool = Field(
        default=True,
        description="If True, any CRITICAL severity issue causes immediate pipeline failure.",
    )

    VALIDATOR_STAGE_TIMEOUT_SECONDS: int = Field(
        default=30,
        description="Timeout per validator stage in seconds.",
    )

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


validation_settings = ValidationPipelineSettings()
