"""
MetricsService Tests — Phase 5.10
"""
import pytest
from portfolio.services.metrics_service import metrics_service


@pytest.mark.asyncio
async def test_calculate_metrics():
    metrics = await metrics_service.calculate_metrics(project_id=1)
    assert metrics.lines_of_code == 3450
    assert metrics.quality_grade == "A+"
    assert metrics.validation_score == 96.5
