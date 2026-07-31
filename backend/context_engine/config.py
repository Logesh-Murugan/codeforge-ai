"""
Context Engine Settings — Phase 5.5

Tunables, quality thresholds, freshness decay rates, and context expiry limits.
"""
from __future__ import annotations

from typing import Dict, List
from pydantic import Field
from pydantic_settings import BaseSettings


class ContextEngineSettings(BaseSettings):
    """
    Configuration settings for the Context Sharing Engine.
    """

    CONTEXT_TTL_HOURS: int = Field(
        default=24,
        description="Default expiration time for cached context entries (in hours).",
    )

    CONTEXT_MIN_QUALITY_SCORE: float = Field(
        default=0.6,
        description="Minimum overall context quality score threshold.",
    )

    CONTEXT_FRESHNESS_DECAY_RATE: float = Field(
        default=0.1,
        description="Time decay rate for context freshness calculation.",
    )

    # 21 Supported Context Types
    ALL_CONTEXT_TYPES: List[str] = Field(
        default=[
            "Project",
            "Requirement",
            "Architecture",
            "Memory",
            "RAG",
            "Human Approval",
            "Agent",
            "Workflow",
            "Timeline",
            "Validation",
            "Security",
            "Testing",
            "Documentation",
            "Deployment",
            "Export",
            "Generated Files",
            "Frontend",
            "Backend",
            "Database",
            "API",
            "Collaboration",
        ],
        description="Supported 21 Context Types.",
    )

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


context_settings = ContextEngineSettings()
