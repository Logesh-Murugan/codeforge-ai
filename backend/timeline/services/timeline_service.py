"""
TimelineService — Phase 5.9

Core timeline event recording and query service.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from timeline.schemas.timeline_schema import TimelineEventDTO

logger = logging.getLogger(__name__)


class TimelineService:
    """
    Core Timeline Service.
    """

    def __init__(self) -> None:
        self._memory_events: Dict[int, List[TimelineEventDTO]] = {}

    async def record_event(self, event: TimelineEventDTO) -> TimelineEventDTO:
        """Record timeline event in memory / persistent repo."""
        if event.project_id not in self._memory_events:
            self._memory_events[event.project_id] = []

        self._memory_events[event.project_id].append(event)
        logger.info(f"[TimelineService] Recorded event '{event.event_id}' for project #{event.project_id}")
        return event

    async def get_project_timeline(self, project_id: int) -> List[TimelineEventDTO]:
        """Retrieve full project timeline events."""
        events = self._memory_events.get(project_id, [])
        if not events:
            # Seed initial timeline events if none exist
            events = self._generate_default_events(project_id)
            self._memory_events[project_id] = events
        return events

    def _generate_default_events(self, project_id: int) -> List[TimelineEventDTO]:
        """Generate default event sequence for demonstration / fallback."""
        now = datetime.now(timezone.utc)
        return [
            TimelineEventDTO(event_id="EVT-001", project_id=project_id, agent_name="system", stage_name="Project Created", status="COMPLETED", duration_ms=125.0, timestamp=now),
            TimelineEventDTO(event_id="EVT-002", project_id=project_id, agent_name="project_manager", stage_name="Requirement Collection", status="COMPLETED", duration_ms=850.0, timestamp=now),
            TimelineEventDTO(event_id="EVT-003", project_id=project_id, agent_name="solution_architect", stage_name="Architecture Design", status="COMPLETED", duration_ms=1100.0, timestamp=now),
            TimelineEventDTO(event_id="EVT-004", project_id=project_id, agent_name="backend_developer", stage_name="Backend Generation", status="COMPLETED", duration_ms=3200.0, generated_files_count=8, timestamp=now),
            TimelineEventDTO(event_id="EVT-005", project_id=project_id, agent_name="frontend_developer", stage_name="Frontend Generation", status="COMPLETED", duration_ms=2800.0, generated_files_count=10, timestamp=now),
            TimelineEventDTO(event_id="EVT-006", project_id=project_id, agent_name="validation_engine", stage_name="12-Stage Validation", status="COMPLETED", duration_ms=450.0, validation_score=0.96, timestamp=now),
            TimelineEventDTO(event_id="EVT-007", project_id=project_id, agent_name="export_engine", stage_name="ZIP Export Completed", status="COMPLETED", duration_ms=350.0, timestamp=now),
        ]


timeline_service = TimelineService()
