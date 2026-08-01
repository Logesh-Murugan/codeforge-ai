"""
EventBus Tests — Phase 5.7
"""
import pytest
from monitoring.events.event_bus import EventBus
from monitoring.schemas.events import MonitoringEventPayload, MonitoringEventType


@pytest.mark.asyncio
async def test_event_bus_publish_subscribe():
    bus = EventBus()
    received_events = []

    async def handler(event: MonitoringEventPayload):
        received_events.append(event)

    bus.subscribe(MonitoringEventType.WORKFLOW_STARTED, handler)

    payload = MonitoringEventPayload(
        project_id=1,
        event_type=MonitoringEventType.WORKFLOW_STARTED,
        message="Workflow starting test",
    )
    await bus.publish(payload)

    assert len(received_events) == 1
    assert received_events[0].event_type == MonitoringEventType.WORKFLOW_STARTED
    assert received_events[0].message == "Workflow starting test"
