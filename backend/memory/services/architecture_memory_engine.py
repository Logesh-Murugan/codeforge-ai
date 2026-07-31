"""
ArchitectureMemoryEngine — Phase 5.1

Domain-specific memory engine for architecture decisions, component
definitions, design patterns, and tech-stack records.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from memory.persistent_schemas import MemoryCategory, PersistentMemoryResponse
from memory.services.base_memory_service import BaseMemoryEngine

logger = logging.getLogger(__name__)


class ArchitectureMemoryEngine(BaseMemoryEngine):
    """Engine for architecture memory entries."""

    CATEGORY = MemoryCategory.ARCHITECTURE
    DOMAIN_FIELDS = [
        "component_name", "pattern", "tech_stack",
        "layer", "diagram_url", "decision_rationale",
    ]

    async def get_by_component(
        self,
        project_id: int,
        component_name: str,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryResponse]:
        """Retrieve all entries for a specific architecture component."""
        entries = await self.list_entries(project_id=project_id, session=session)
        return [
            e for e in entries
            if e.metadata_json.get("component_name") == component_name
        ]

    async def get_by_layer(
        self,
        project_id: int,
        layer: str,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryResponse]:
        """Retrieve entries filtered by architecture layer."""
        entries = await self.list_entries(project_id=project_id, session=session)
        return [
            e for e in entries
            if e.metadata_json.get("layer") == layer
        ]

    async def get_by_pattern(
        self,
        project_id: int,
        pattern: str,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryResponse]:
        """Retrieve entries matching a design pattern."""
        entries = await self.list_entries(project_id=project_id, session=session)
        return [
            e for e in entries
            if e.metadata_json.get("pattern") == pattern
        ]

    async def get_architecture_summary(
        self,
        project_id: int,
        session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Aggregate architecture summary grouped by layer and pattern."""
        entries = await self.list_entries(
            project_id=project_id, limit=500, session=session,
        )
        by_layer: Dict[str, int] = {}
        by_pattern: Dict[str, int] = {}
        components: List[str] = []
        tech_set: set = set()

        for e in entries:
            meta = e.metadata_json
            layer = meta.get("layer", "unspecified")
            by_layer[layer] = by_layer.get(layer, 0) + 1
            pattern = meta.get("pattern")
            if pattern:
                by_pattern[pattern] = by_pattern.get(pattern, 0) + 1
            comp = meta.get("component_name")
            if comp:
                components.append(comp)
            for t in meta.get("tech_stack", []) or []:
                tech_set.add(t)

        return {
            "total": len(entries),
            "by_layer": by_layer,
            "by_pattern": by_pattern,
            "components": sorted(set(components)),
            "tech_stack": sorted(tech_set),
        }
