"""
ModelManager — Phase 5.6

Manages LLM enumeration, validation, capabilities, and alternative recommendations.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from ai_mode_manager.config.ai_config import ai_config
from ai_mode_manager.registry.provider_registry import provider_registry
from ai_mode_manager.schemas.mode_state import WorkingMode
from ai_mode_manager.schemas.request_response import ModelInfoResponse

logger = logging.getLogger(__name__)


class ModelManager:
    """
    LLM Model Manager.
    """

    def list_available_models(self, mode: Optional[WorkingMode] = None) -> List[ModelInfoResponse]:
        """List all supported LLM models for the specified or active mode."""
        active_mode = mode or ai_config.CURRENT_MODE
        if active_mode == WorkingMode.LOCAL:
            models = ai_config.LOCAL_LLMS
            provider_name = "ollama"
        else:
            models = ai_config.CLOUD_LLMS
            provider_name = "groq"

        return [
            ModelInfoResponse(
                name=m,
                provider=provider_name,
                is_recommended=(m in ("llama-3.1-8b", "qwen2.5-coder")),
            )
            for m in models
        ]

    def get_current_model(self) -> str:
        """Return currently configured active model."""
        return ai_config.CURRENT_MODEL

    def validate_model(self, model_name: str, mode: Optional[WorkingMode] = None) -> bool:
        """Check if model is supported in mode."""
        active_mode = mode or ai_config.CURRENT_MODE
        allowed = (
            ai_config.LOCAL_LLMS if active_mode == WorkingMode.LOCAL else ai_config.CLOUD_LLMS
        )
        return model_name in allowed

    def recommend_alternative_model(self, model_name: str, mode: Optional[WorkingMode] = None) -> str:
        """Recommend supported fallback model if requested model is unavailable."""
        active_mode = mode or ai_config.CURRENT_MODE
        return "qwen2.5-coder" if active_mode == WorkingMode.LOCAL else "llama-3.1-8b"
