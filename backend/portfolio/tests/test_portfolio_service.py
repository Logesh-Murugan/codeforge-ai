"""
PortfolioService Tests — Phase 5.10
"""
import pytest
from portfolio.services.portfolio_service import portfolio_service


@pytest.mark.asyncio
async def test_get_portfolio():
    pf = await portfolio_service.get_portfolio(project_id=1)
    assert pf.project_id == 1
    assert pf.metrics.lines_of_code > 0
    assert len(pf.agent_workflows) == 13
    assert len(pf.downloads) >= 1
