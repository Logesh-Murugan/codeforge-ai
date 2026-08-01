"""
Monitoring Event Bus — Phase 5.7

Asynchronous event bus for publishing live monitoring events across all system components.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Callable, Dict, List, Optional

from monitoring.schemas.events import MonitoringEventPayload, MonitoringEventType

logger = logging.getLogger(__name__)


class EventBus:
    """
    Monitoring Event Bus (Publish/Subscribe).
    """

    def __init__(self) -> None:
        self._subscribers: Dict[MonitoringEventType, List[Callable]] = {}

    def subscribe(self, event_type: MonitoringEventType, handler: Callable) -> None:
        """Subscribe handler function to specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    async def publish(self, event: MonitoringEventPayload) -> None:
        """Publish monitoring event to all registered subscribers."""
        logger.info(f"[EventBus] Emitting event '{event.event_type.value}' for project {event.project_id}")

        handlers = self._subscribers.get(event.event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as exc:
                logger.error(f"[EventBus] Error executing subscriber handler: {exc}")


event_bus = EventBus()
