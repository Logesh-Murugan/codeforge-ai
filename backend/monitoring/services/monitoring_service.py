"""
MonitoringService — Phase 5.7

Unified facade service for Real-Time Monitoring System.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from monitoring.collectors.execution_collector import ExecutionCollector
from monitoring.collectors.metrics_collector import MetricsCollector
from monitoring.services.log_service import LogService
from monitoring.services.timeline_service import TimelineService

logger = logging.getLogger(__name__)


class MonitoringService:
    """
    Monitoring Service Facade.
    """

    def __init__(self) -> None:
        self.collector = ExecutionCollector()
        self.metrics_collector = MetricsCollector()
        self.timeline_service = TimelineService()
        self.log_service = LogService()

    async def get_dashboard_summary(self, project_id: int) -> Dict[str, Any]:
        """
        Return comprehensive monitoring dashboard payload.
        """
        status_dto = await self.collector.collect_workflow_status(project_id)
        metrics_dto = await self.metrics_collector.collect_metrics(project_id)
        timeline = await self.timeline_service.get_project_timeline(project_id)
        logs = await self.log_service.get_live_logs(project_id)

        return {
            "project_id": project_id,
            "status": status_dto.model_dump(),
            "metrics": metrics_dto.model_dump(),
            "timeline": timeline,
            "logs": logs,
        }
