"""
DatabaseMemoryEngine — Phase 5.1

Domain-specific memory engine for database schemas, table definitions,
migrations, and indexing strategies.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from memory.persistent_schemas import MemoryCategory, PersistentMemoryResponse
from memory.services.base_memory_service import BaseMemoryEngine

logger = logging.getLogger(__name__)


class DatabaseMemoryEngine(BaseMemoryEngine):
    """Engine for database memory entries."""

    CATEGORY = MemoryCategory.DATABASE
    DOMAIN_FIELDS = [
        "schema_definition", "table_name", "relationships",
        "migration_status", "db_engine", "indexes",
    ]

    def _pre_create(
        self,
        content: str,
        metadata: Dict[str, Any],
        domain_fields: Dict[str, Any],
    ) -> tuple[str, Dict[str, Any]]:
        """Default migration_status to 'pending' if not specified."""
        if "migration_status" not in metadata:
            metadata["migration_status"] = "pending"
        if "db_engine" not in metadata:
            metadata["db_engine"] = "postgresql"
        return content, metadata

    async def get_by_table(
        self,
        project_id: int,
        table_name: str,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryResponse]:
        """Retrieve entries for a specific table."""
        entries = await self.list_entries(project_id=project_id, session=session)
        return [
            e for e in entries
            if e.metadata_json.get("table_name") == table_name
        ]

    async def get_by_migration_status(
        self,
        project_id: int,
        status: str,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryResponse]:
        """Retrieve entries filtered by migration status."""
        entries = await self.list_entries(project_id=project_id, session=session)
        return [
            e for e in entries
            if e.metadata_json.get("migration_status") == status
        ]

    async def get_schema_map(
        self,
        project_id: int,
        session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Build a map of all tables, relationships, and indexes."""
        entries = await self.list_entries(
            project_id=project_id, limit=500, session=session,
        )
        tables: List[str] = []
        all_relationships: List[str] = []
        all_indexes: List[str] = []
        by_status: Dict[str, int] = {}

        for e in entries:
            meta = e.metadata_json
            tbl = meta.get("table_name")
            if tbl:
                tables.append(tbl)
            for rel in meta.get("relationships", []) or []:
                all_relationships.append(rel)
            for idx in meta.get("indexes", []) or []:
                all_indexes.append(idx)
            s = meta.get("migration_status", "unknown")
            by_status[s] = by_status.get(s, 0) + 1

        return {
            "total": len(entries),
            "tables": sorted(set(tables)),
            "relationships": all_relationships,
            "indexes": all_indexes,
            "by_migration_status": by_status,
        }
