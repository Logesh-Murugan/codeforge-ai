"""
ProviderManager — Phase 5.6

Provider lifecycle & fallback strategy validator.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from ai_mode_manager.config.ai_config import ai_config
from ai_mode_manager.providers.base_provider import AIProvider
from ai_mode_manager.registry.provider_registry import provider_registry
from ai_mode_manager.schemas.mode_state import HealthStatus, WorkingMode

logger = logging.getLogger(__name__)


class ProviderManager:
    """
    Provider Lifecycle & Fallback Strategy Manager.
    """

    def get_active_provider(self) -> Optional[AIProvider]:
        """Get current active provider instance."""
        return provider_registry.get_provider(ai_config.CURRENT_PROVIDER)

    def validate_provider_availability(self, provider_id: str) -> Dict[str, Any]:
        """
        Validate provider availability.
        If unavailable, returns structured error with alternative recommendations.
        """
        exists = provider_registry.provider_exists(provider_id)
        if not exists:
            return {
                "available": False,
                "error": f"Provider '{provider_id}' is not registered.",
                "recommendation": "Use 'groq' for CLOUD mode or 'ollama' for LOCAL mode.",
            }
        return {"available": True, "provider_id": provider_id}
