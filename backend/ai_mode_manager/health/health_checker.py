"""
ProviderHealthChecker — Phase 5.6

Health Monitoring System for AI Providers, reachability, model availability, and configuration integrity.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from ai_mode_manager.config.ai_config import ai_config
from ai_mode_manager.registry.provider_registry import provider_registry
from ai_mode_manager.schemas.mode_state import HealthStatus, WorkingMode

logger = logging.getLogger(__name__)


class ProviderHealthChecker:
    """
    Health Monitoring System.
    """

    async def check_provider_health(self, provider_id: str) -> HealthStatus:
        """Check health status of a specific provider."""
        provider = provider_registry.get_provider(provider_id)
        if not provider:
            return HealthStatus.UNAVAILABLE
        return await provider.check_health()

    async def check_all_providers_health(self) -> Dict[str, HealthStatus]:
        """Check health status of all registered providers."""
        results: Dict[str, HealthStatus] = {}
        for provider in provider_registry.list_providers():
            try:
                status = await provider.check_health()
                results[provider.name] = status
            except Exception as exc:
                logger.warning(f"[HealthChecker] Exception checking '{provider.name}': {exc}")
                results[provider.name] = HealthStatus.UNAVAILABLE
        return results

    async def get_active_mode_health(self) -> HealthStatus:
        """Get health status of current active provider for active mode."""
        active_provider_id = ai_config.CURRENT_PROVIDER
        return await self.check_provider_health(active_provider_id)
