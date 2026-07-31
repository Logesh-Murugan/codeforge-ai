"""
FrontendMemoryEngine — Phase 5.1

Domain-specific memory engine for frontend components, routes,
styling approaches, and framework tracking.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from memory.persistent_schemas import MemoryCategory, PersistentMemoryResponse
from memory.services.base_memory_service import BaseMemoryEngine

logger = logging.getLogger(__name__)


class FrontendMemoryEngine(BaseMemoryEngine):
    """Engine for frontend memory entries."""

    CATEGORY = MemoryCategory.FRONTEND
    DOMAIN_FIELDS = [
        "file_path", "language", "framework",
        "component_name", "component_type", "styling", "route_path",
    ]

    async def get_by_component(
        self,
        project_id: int,
        component_name: str,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryResponse]:
        """Retrieve entries for a specific component."""
        entries = await self.list_entries(project_id=project_id, session=session)
        return [
            e for e in entries
            if e.metadata_json.get("component_name") == component_name
        ]

    async def get_by_component_type(
        self,
        project_id: int,
        component_type: str,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryResponse]:
        """Retrieve entries filtered by component type (page/layout/widget/hook)."""
        entries = await self.list_entries(project_id=project_id, session=session)
        return [
            e for e in entries
            if e.metadata_json.get("component_type") == component_type
        ]

    async def get_by_route(
        self,
        project_id: int,
        route_path: str,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryResponse]:
        """Retrieve entries for a specific frontend route."""
        entries = await self.list_entries(project_id=project_id, session=session)
        return [
            e for e in entries
            if e.metadata_json.get("route_path") == route_path
        ]

    async def get_component_tree(
        self,
        project_id: int,
        session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Build a tree of all components grouped by type and framework."""
        entries = await self.list_entries(
            project_id=project_id, limit=500, session=session,
        )
        by_type: Dict[str, List[str]] = {}
        routes: List[str] = []
        by_framework: Dict[str, int] = {}
        by_styling: Dict[str, int] = {}

        for e in entries:
            meta = e.metadata_json
            ct = meta.get("component_type", "unspecified")
            name = meta.get("component_name", "unnamed")
            by_type.setdefault(ct, []).append(name)
            rp = meta.get("route_path")
            if rp:
                routes.append(rp)
            fw = meta.get("framework")
            if fw:
                by_framework[fw] = by_framework.get(fw, 0) + 1
            st = meta.get("styling")
            if st:
                by_styling[st] = by_styling.get(st, 0) + 1

        return {
            "total": len(entries),
            "by_component_type": by_type,
            "routes": sorted(set(routes)),
            "by_framework": by_framework,
            "by_styling": by_styling,
        }
