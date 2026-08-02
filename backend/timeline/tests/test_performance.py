"""
Performance Tests — Phase 5.9
"""
import time
import pytest
from timeline.services.timeline_service import timeline_service


@pytest.mark.asyncio
async def test_timeline_performance():
    t0 = time.perf_counter()
    events = await timeline_service.get_project_timeline(project_id=1)
    duration_ms = (time.perf_counter() - t0) * 1000.0

    assert len(events) > 0
    assert duration_ms < 50.0  # Timeline fetch must complete in <50ms
