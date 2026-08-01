"""
Performance Tests — Phase 5.7
"""
import time
import pytest
from monitoring.collectors.execution_collector import ExecutionCollector


@pytest.mark.asyncio
async def test_collector_performance():
    collector = ExecutionCollector()
    t0 = time.perf_counter()
    status = await collector.collect_workflow_status(project_id=1)
    duration_ms = (time.perf_counter() - t0) * 1000.0

    assert status is not None
    assert duration_ms < 50.0  # Collector must execute in <50ms
