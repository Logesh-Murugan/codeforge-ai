"""
Performance Tests — Phase 5.4

Verifies fast async execution of collaboration analytics and context assembly (<500ms).
"""
import time
import pytest
from collaboration.services.analytics_service import AnalyticsService
from collaboration.services.context_exchange_service import ContextExchangeService


@pytest.mark.asyncio
async def test_analytics_service_performance():
    service = AnalyticsService()
    start = time.time()
    res = await service.get_collaboration_status(42)
    elapsed = time.time() - start

    assert res.project_id == 42
    assert elapsed < 0.5  # Must execute under 500ms


@pytest.mark.asyncio
async def test_context_exchange_performance():
    service = ContextExchangeService()
    start = time.time()
    res = await service.assemble_context_bundle(42, "backend_developer")
    elapsed = time.time() - start

    assert res.project_id == 42
    assert elapsed < 0.5  # Must execute under 500ms
