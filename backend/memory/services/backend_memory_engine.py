"""
BackendMemoryEngine — Phase 5.1

Domain-specific memory engine for backend source code, modules,
services, and dependency tracking.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from memory.persistent_schemas import MemoryCategory, PersistentMemoryResponse
from memory.services.base_memory_service import BaseMemoryEngine

logger = logging.getLogger(__name__)


class BackendMemoryEngine(BaseMemoryEngine):
    """Engine for backend memory entries."""

    CATEGORY = MemoryCategory.BACKEND
    DOMAIN_FIELDS = [
        "file_path", "language", "framework",
        "module_name", "dependencies", "code_type",
    ]

    def _pre_create(
        self,
        content: str,
        metadata: Dict[str, Any],
        domain_fields: Dict[str, Any],
    ) -> tuple[str, Dict[str, Any]]:
        """Default language to 'python' if not specified."""
        if "language" not in metadata:
            metadata["language"] = "python"
        return content, metadata

    async def get_by_module(
        self,
        project_id: int,
        module_name: str,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryResponse]:
        """Retrieve all entries for a specific module."""
        entries = await self.list_entries(project_id=project_id, session=session)
        return [
            e for e in entries
            if e.metadata_json.get("module_name") == module_name
        ]

    async def get_by_code_type(
        self,
        project_id: int,
        code_type: str,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryResponse]:
        """Retrieve entries filtered by code type (model/service/route/util)."""
        entries = await self.list_entries(project_id=project_id, session=session)
        return [
            e for e in entries
            if e.metadata_json.get("code_type") == code_type
        ]

    async def get_dependency_map(
        self,
        project_id: int,
        session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Build a map of all modules, code types, and dependencies."""
        entries = await self.list_entries(
            project_id=project_id, limit=500, session=session,
        )
        modules: List[str] = []
        all_deps: set = set()
        by_type: Dict[str, int] = {}
        by_framework: Dict[str, int] = {}

        for e in entries:
            meta = e.metadata_json
            mod = meta.get("module_name")
            if mod:
                modules.append(mod)
            for dep in meta.get("dependencies", []) or []:
                all_deps.add(dep)
            ct = meta.get("code_type", "unspecified")
            by_type[ct] = by_type.get(ct, 0) + 1
            fw = meta.get("framework")
            if fw:
                by_framework[fw] = by_framework.get(fw, 0) + 1

        return {
            "total": len(entries),
            "modules": sorted(set(modules)),
            "dependencies": sorted(all_deps),
            "by_code_type": by_type,
            "by_framework": by_framework,
        }
