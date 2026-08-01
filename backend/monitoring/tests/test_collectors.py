"""
Collectors Tests — Phase 5.7
"""
import pytest
from monitoring.collectors.execution_collector import ExecutionCollector
from monitoring.collectors.metrics_collector import MetricsCollector


@pytest.mark.asyncio
async def test_execution_collector():
    collector = ExecutionCollector()
    status = await collector.collect_workflow_status(project_id=1)
    assert status.project_id == 1
    assert len(status.agents) == 13


@pytest.mark.asyncio
async def test_metrics_collector():
    collector = MetricsCollector()
    metrics = await collector.collect_metrics(project_id=1)
    assert metrics.project_id == 1
    assert metrics.success_rate_pct == 100.0
