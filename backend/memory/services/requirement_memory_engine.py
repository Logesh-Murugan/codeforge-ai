"""
RequirementMemoryEngine — Phase 5.1

Domain-specific memory engine for requirements with priority tracking,
acceptance criteria, and stakeholder management.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from memory.persistent_schemas import MemoryCategory, PersistentMemoryResponse
from memory.services.base_memory_service import BaseMemoryEngine

logger = logging.getLogger(__name__)


class RequirementMemoryEngine(BaseMemoryEngine):
    """Engine for requirement memory entries."""

    CATEGORY = MemoryCategory.REQUIREMENT
    DOMAIN_FIELDS = [
        "priority", "status", "acceptance_criteria",
        "stakeholder", "requirement_type", "user_story",
    ]

    def _pre_create(
        self,
        content: str,
        metadata: Dict[str, Any],
        domain_fields: Dict[str, Any],
    ) -> tuple[str, Dict[str, Any]]:
        """Default priority to 'medium' if not specified."""
        if "priority" not in metadata:
            metadata["priority"] = "medium"
        if "status" not in metadata:
            metadata["status"] = "draft"
        return content, metadata

    async def get_by_priority(
        self,
        project_id: int,
        priority: str,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryResponse]:
        """Retrieve all requirements with a specific priority level."""
        entries = await self.list_entries(project_id=project_id, session=session)
        return [
            e for e in entries
            if e.metadata_json.get("priority") == priority
        ]

    async def get_by_status(
        self,
        project_id: int,
        status: str,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryResponse]:
        """Retrieve all requirements with a specific status."""
        entries = await self.list_entries(project_id=project_id, session=session)
        return [
            e for e in entries
            if e.metadata_json.get("status") == status
        ]

    async def get_requirements_summary(
        self,
        project_id: int,
        session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """
        Aggregate summary of requirements by priority and status.
        """
        entries = await self.list_entries(
            project_id=project_id, limit=500, session=session,
        )
        by_priority: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        for e in entries:
            meta = e.metadata_json
            p = meta.get("priority", "unset")
            s = meta.get("status", "unset")
            by_priority[p] = by_priority.get(p, 0) + 1
            by_status[s] = by_status.get(s, 0) + 1

        return {
            "total": len(entries),
            "by_priority": by_priority,
            "by_status": by_status,
        }
