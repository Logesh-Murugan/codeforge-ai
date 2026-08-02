"""
Timeline Configuration — Phase 5.9
"""
from __future__ import annotations

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class TimelineSettings(BaseSettings):
    """
    Settings for Project Timeline System.
    """

    MAX_TIMELINE_HISTORY_EVENTS: int = Field(
        default=5000,
        description="Maximum timeline events retained per project.",
    )

    AUTO_DETECT_MILESTONES: bool = Field(
        default=True,
        description="Automatically trigger milestone detection on event updates.",
    )

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


timeline_settings = TimelineSettings()
