"""
Verification Suite — Phase 5.7 Real-Time Monitoring System
"""
import asyncio
import sys

from monitoring.config import monitoring_settings
from monitoring.events.event_bus import EventBus, event_bus
from monitoring.schemas.events import MonitoringEventPayload, MonitoringEventType
from monitoring.collectors.execution_collector import ExecutionCollector
from monitoring.collectors.metrics_collector import MetricsCollector
from monitoring.metrics.metrics_engine import MetricsEngine
from monitoring.services.monitoring_service import MonitoringService
from monitoring.services.timeline_service import TimelineService
from monitoring.services.log_service import LogService
from monitoring.websocket.connection_manager import ConnectionManager


async def run_all_tests():
    print("--- 1. Testing Monitoring Config ---")
    assert len(monitoring_settings.ALL_13_AGENTS) == 13
    assert "project_manager" in monitoring_settings.ALL_13_AGENTS
    assert "devops_engineer" in monitoring_settings.ALL_13_AGENTS
    print("Config tests PASSED [OK]")

    print("\n--- 2. Testing EventBus Publish/Subscribe ---")
    received = []

    async def h(e):
        received.append(e)

    event_bus.subscribe(MonitoringEventType.WORKFLOW_STARTED, h)
    payload = MonitoringEventPayload(
        project_id=1,
        event_type=MonitoringEventType.WORKFLOW_STARTED,
        message="Workflow started test",
    )
    await event_bus.publish(payload)
    assert len(received) == 1
    assert received[0].message == "Workflow started test"
    print("EventBus tests PASSED [OK]")

    print("\n--- 3. Testing ExecutionCollector (13 Agents) ---")
    col = ExecutionCollector()
    status_dto = await col.collect_workflow_status(project_id=1)
    assert status_dto.project_id == 1
    assert len(status_dto.agents) == 13
    assert status_dto.total_steps == 13
    print("ExecutionCollector tests PASSED [OK]")

    print("\n--- 4. Testing MetricsCollector & MetricsEngine ---")
    m_col = MetricsCollector()
    metrics = await m_col.collect_metrics(project_id=1)
    assert metrics.project_id == 1
    assert metrics.success_rate_pct == 100.0

    eng = MetricsEngine()
    assert eng.calculate_success_rate(10, 2) == 80.0
    print("Metrics tests PASSED [OK]")

    print("\n--- 5. Testing MonitoringService Facade & Timeline/Log Services ---")
    service = MonitoringService()
    dash = await service.get_dashboard_summary(project_id=1)
    assert "status" in dash
    assert "metrics" in dash
    assert "timeline" in dash
    assert "logs" in dash
    print("Service facade tests PASSED [OK]")

    print("\n--- 6. Testing WebSocket ConnectionManager ---")
    cm = ConnectionManager()
    assert len(cm.active_connections) == 0
    print("WebSocket ConnectionManager tests PASSED [OK]")

    print("\n==========================================")
    print("ALL PHASE 5.7 MONITORING TESTS PASSED SUCCESSFULLY! [OK]")
    print("==========================================")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
