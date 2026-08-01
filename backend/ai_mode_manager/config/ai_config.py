"""
AIConfiguration System — Phase 5.6

Manages system-wide AI Mode settings, active provider, model selection, and health state.
"""
from __future__ import annotations

import os
from typing import Dict, List
from pydantic import Field
from pydantic_settings import BaseSettings

from ai_mode_manager.schemas.mode_state import HealthStatus, WorkingMode


class AIConfiguration(BaseSettings):
    """
    AI Mode Manager Configuration state.
    """

    CURRENT_MODE: WorkingMode = Field(
        default=WorkingMode.CLOUD,
        description="Active AI Mode (local or cloud).",
    )

    CURRENT_PROVIDER: str = Field(
        default="groq",
        description="Active provider identifier.",
    )

    CURRENT_MODEL: str = Field(
        default="llama-3.1-8b",
        description="Active LLM model.",
    )

    CURRENT_EMBEDDING: str = Field(
        default="all-MiniLM-L6-v2",
        description="Active embedding model.",
    )

    OLLAMA_BASE_URL: str = Field(
        default="http://localhost:11434",
        description="Base URL for Ollama local service.",
    )

    GROQ_API_KEY: str = Field(
        default="",
        description="API Key for Groq cloud service.",
    )

    HEALTH_STATUS: HealthStatus = Field(
        default=HealthStatus.CONNECTED,
        description="Current provider health status.",
    )

    LOCAL_LLMS: List[str] = Field(
        default=["qwen2.5-coder", "deepseek-r1", "llama3.1", "mistral", "phi3", "gemma"],
    )

    LOCAL_EMBEDDINGS: List[str] = Field(
        default=["nomic-embed-text", "bge-small", "all-minilm"],
    )

    CLOUD_LLMS: List[str] = Field(
        default=["llama-3.1-8b", "llama-3.3-70b", "deepseek-r1", "mixtral", "gemma"],
    )

    CLOUD_EMBEDDINGS: List[str] = Field(
        default=["all-MiniLM-L6-v2", "bge-small-en", "gte-small"],
    )

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


ai_config = AIConfiguration()
