"""
Performance Tests — Phase 5.10
"""
import time
import pytest
from portfolio.services.portfolio_service import portfolio_service


@pytest.mark.asyncio
async def test_portfolio_performance():
    t0 = time.perf_counter()
    pf = await portfolio_service.get_portfolio(project_id=1)
    duration_ms = (time.perf_counter() - t0) * 1000.0

    assert pf is not None
    assert duration_ms < 100.0  # Full portfolio generation in <100ms
