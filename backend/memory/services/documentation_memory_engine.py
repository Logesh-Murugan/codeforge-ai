"""
DocumentationMemoryEngine — Phase 5.1

Domain-specific memory engine for documentation artifacts, including
README files, API docs, ADRs, changelogs, and user guides.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from memory.persistent_schemas import MemoryCategory, PersistentMemoryResponse
from memory.services.base_memory_service import BaseMemoryEngine

logger = logging.getLogger(__name__)


class DocumentationMemoryEngine(BaseMemoryEngine):
    """Engine for documentation memory entries."""

    CATEGORY = MemoryCategory.DOCUMENTATION
    DOMAIN_FIELDS = [
        "doc_type", "audience", "doc_format",
        "sections", "related_files", "auto_generated",
    ]

    async def get_by_doc_type(
        self,
        project_id: int,
        doc_type: str,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryResponse]:
        """Retrieve entries filtered by document type (readme/api-docs/guide)."""
        entries = await self.list_entries(project_id=project_id, session=session)
        return [
            e for e in entries
            if e.metadata_json.get("doc_type") == doc_type
        ]

    async def get_by_audience(
        self,
        project_id: int,
        audience: str,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryResponse]:
        """Retrieve entries targeted at a specific audience."""
        entries = await self.list_entries(project_id=project_id, session=session)
        return [
            e for e in entries
            if e.metadata_json.get("audience") == audience
        ]

    async def get_documentation_index(
        self,
        project_id: int,
        session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Build a documentation index grouped by type and audience."""
        entries = await self.list_entries(
            project_id=project_id, limit=500, session=session,
        )
        by_type: Dict[str, int] = {}
        by_audience: Dict[str, int] = {}
        by_format: Dict[str, int] = {}
        auto_count = 0
        all_related: set = set()

        for e in entries:
            meta = e.metadata_json
            dt = meta.get("doc_type", "unspecified")
            by_type[dt] = by_type.get(dt, 0) + 1
            aud = meta.get("audience")
            if aud:
                by_audience[aud] = by_audience.get(aud, 0) + 1
            fmt = meta.get("doc_format")
            if fmt:
                by_format[fmt] = by_format.get(fmt, 0) + 1
            if meta.get("auto_generated"):
                auto_count += 1
            for rf in meta.get("related_files", []) or []:
                all_related.add(rf)

        return {
            "total": len(entries),
            "by_doc_type": by_type,
            "by_audience": by_audience,
            "by_format": by_format,
            "auto_generated_count": auto_count,
            "related_files": sorted(all_related),
        }
