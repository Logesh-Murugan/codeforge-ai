"""
ProjectMemoryEngine — Phase 5.1

Domain-specific memory engine for project-level memory (milestones,
phases, status, high-level project history).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from memory.persistent_schemas import MemoryCategory, PersistentMemoryResponse
from memory.services.base_memory_service import BaseMemoryEngine

logger = logging.getLogger(__name__)


class ProjectMemoryEngine(BaseMemoryEngine):
    """Engine for project-level memory entries."""

    CATEGORY = MemoryCategory.PROJECT
    DOMAIN_FIELDS = [
        "project_phase", "milestone", "status", "priority", "tags",
    ]

    async def get_by_phase(
        self,
        project_id: int,
        phase: str,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryResponse]:
        """Retrieve all entries for a specific project phase."""
        entries = await self.list_entries(project_id=project_id, session=session)
        return [
            e for e in entries
            if e.metadata_json.get("project_phase") == phase
        ]

    async def get_by_milestone(
        self,
        project_id: int,
        milestone: str,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryResponse]:
        """Retrieve all entries for a specific milestone."""
        entries = await self.list_entries(project_id=project_id, session=session)
        return [
            e for e in entries
            if e.metadata_json.get("milestone") == milestone
        ]

    async def get_project_timeline(
        self,
        project_id: int,
        session: Optional[AsyncSession] = None,
    ) -> List[Dict[str, Any]]:
        """
        Build a chronological timeline of project memory entries.
        Returns entries sorted by creation date with extracted domain fields.
        """
        entries = await self.list_entries(
            project_id=project_id, limit=500, session=session,
        )
        timeline = [self.enrich_response(e) for e in entries]
        timeline.sort(key=lambda x: x.get("created_at", ""))
        return timeline
