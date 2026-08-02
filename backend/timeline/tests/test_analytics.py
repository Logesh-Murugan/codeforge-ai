"""
AnalyticsService Tests — Phase 5.9
"""
import pytest
from timeline.services.analytics_service import AnalyticsService
from timeline.services.progress_service import ProgressService


@pytest.mark.asyncio
async def test_analytics_service():
    service = AnalyticsService()
    analytics = await service.get_project_analytics(project_id=1)
    assert analytics.project_id == 1
    assert analytics.total_events > 0
    assert analytics.average_runtime_ms > 0.0


@pytest.mark.asyncio
async def test_progress_service():
    service = ProgressService()
    prog = await service.get_project_progress(project_id=1)
    assert prog.project_id == 1
    assert prog.overall_progress_pct == 100.0
    assert prog.completed_stages_count == 13
