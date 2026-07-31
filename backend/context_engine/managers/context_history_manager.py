"""
ContextHistoryManager — Phase 5.5

Context History System tracking:
- Creation Time
- Updates
- Consumers
- Producers
- Versions
- Usage History
- Changes
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import select

from app.db import AsyncSessionLocal
from context_engine.models.context_history import ContextHistory
from context_engine.schemas.analytics import ContextHistoryRecord

logger = logging.getLogger(__name__)


class ContextHistoryManager:
    """
    Context History System Manager.
    """

    async def log_event(
        self,
        project_id: int,
        context_type: str,
        producer_agent: str,
        action: str,
        context_id: Optional[int] = None,
        consumer_agent: Optional[str] = None,
        version: int = 1,
        change_summary: Optional[str] = None,
    ) -> ContextHistoryRecord:
        """
        Record a context history audit event.
        """
        async with AsyncSessionLocal() as session:
            history_entry = ContextHistory(
                project_id=project_id,
                context_id=context_id,
                context_type=context_type,
                producer_agent=producer_agent,
                consumer_agent=consumer_agent,
                action=action,
                version=version,
                change_summary=change_summary,
            )
            session.add(history_entry)
            await session.commit()
            await session.refresh(history_entry)

            return ContextHistoryRecord(
                id=history_entry.id,
                project_id=history_entry.project_id,
                context_type=history_entry.context_type,
                producer_agent=history_entry.producer_agent,
                consumer_agent=history_entry.consumer_agent,
                action=history_entry.action,
                version=history_entry.version,
                timestamp=history_entry.timestamp,
            )

    async def get_project_history(self, project_id: int) -> List[ContextHistoryRecord]:
        """Fetch complete context usage and version history for a project."""
        async with AsyncSessionLocal() as session:
            res = await session.execute(
                select(ContextHistory)
                .where(ContextHistory.project_id == project_id)
                .order_by(ContextHistory.timestamp)
            )
            rows = res.scalars().all()
            return [
                ContextHistoryRecord(
                    id=row.id,
                    project_id=row.project_id,
                    context_type=row.context_type,
                    producer_agent=row.producer_agent,
                    consumer_agent=row.consumer_agent,
                    action=row.action,
                    version=row.version,
                    timestamp=row.timestamp,
                )
                for row in rows
            ]
