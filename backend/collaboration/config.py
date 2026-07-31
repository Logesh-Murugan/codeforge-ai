"""
Collaboration Settings — Phase 5.4

Configuration settings for the Agent Collaboration Engine.
"""
from __future__ import annotations

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class CollaborationSettings(BaseSettings):
    """
    Tunables and configuration defaults for agent collaboration.
    """

    COLLABORATION_MAX_RETRIES: int = Field(
        default=3,
        description="Maximum retry attempts on cross-agent validation failures.",
    )

    COLLABORATION_DEFAULT_WEIGHT: float = Field(
        default=1.0,
        description="Default weight for agent relationship edges.",
    )

    COLLABORATION_SCORE_THRESHOLD: float = Field(
        default=0.7,
        description="Minimum agreement score threshold for passing cross-validation.",
    )

    # 13 Collaborating Agents
    COLLABORATING_AGENTS: List[str] = Field(
        default=[
            "project_manager",
            "business_analyst",
            "product_owner",
            "solution_architect",
            "database_engineer",
            "api_designer",
            "backend_developer",
            "frontend_developer",
            "security_engineer",
            "qa_engineer",
            "code_reviewer",
            "documentation_writer",
            "devops_engineer",
        ],
        description="Canonical list of all 13 collaborating agents in the platform.",
    )

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


collaboration_settings = CollaborationSettings()
