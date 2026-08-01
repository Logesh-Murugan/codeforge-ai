"""
Health Tests — Phase 5.6
"""
import pytest
from ai_mode_manager.health.health_checker import ProviderHealthChecker


@pytest.mark.asyncio
async def test_health_checker():
    checker = ProviderHealthChecker()
    status_map = await checker.check_all_providers_health()
    assert "groq" in status_map
    assert "ollama" in status_map
