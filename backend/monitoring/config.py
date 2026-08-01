"""
Monitoring Configuration — Phase 5.7
"""
from __future__ import annotations

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class MonitoringSettings(BaseSettings):
    """
    Settings for Real-Time Monitoring System.
    """

    WS_HEARTBEAT_INTERVAL_SECONDS: int = Field(
        default=5,
        description="WebSocket ping/pong heartbeat interval in seconds.",
    )

    MAX_EVENT_HISTORY_BUFFER: int = Field(
        default=1000,
        description="Maximum live event history buffer length per project.",
    )

    MAX_LOG_BUFFER_LINES: int = Field(
        default=500,
        description="Maximum lines kept in live log buffer.",
    )

    ALL_13_AGENTS: List[str] = Field(
        default=[
            "project_manager",
            "business_analyst",
            "product_owner",
            "solution_architect",
            "database_engineer",
            "api_designer",
            "backend_developer",
            "security_engineer",
            "qa_engineer",
            "frontend_developer",
            "code_reviewer",
            "documentation_writer",
            "devops_engineer",
        ],
        description="List of all 13 LangGraph agents.",
    )

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


monitoring_settings = MonitoringSettings()
