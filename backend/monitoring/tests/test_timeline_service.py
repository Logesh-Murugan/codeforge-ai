"""
TimelineService Tests — Phase 5.7
"""
import pytest
from monitoring.services.timeline_service import TimelineService


@pytest.mark.asyncio
async def test_timeline_service():
    service = TimelineService()
    timeline = await service.get_project_timeline(project_id=1)
    assert len(timeline) >= 5
    assert timeline[0]["title"] == "Workflow Started"
