"""
TimelineService Tests — Phase 5.9
"""
import pytest
from timeline.schemas.timeline_schema import TimelineEventDTO
from timeline.services.timeline_service import TimelineService


@pytest.mark.asyncio
async def test_record_and_get_timeline():
    service = TimelineService()
    evt = TimelineEventDTO(
        event_id="EVT-TEST",
        project_id=1,
        agent_name="backend_developer",
        stage_name="Backend Generation",
        status="COMPLETED",
        duration_ms=150.0,
    )
    recorded = await service.record_event(evt)
    assert recorded.event_id == "EVT-TEST"

    events = await service.get_project_timeline(project_id=1)
    assert len(events) >= 1
    assert any(e.event_id == "EVT-TEST" for e in events)
