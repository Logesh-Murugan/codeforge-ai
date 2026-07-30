"""
PersistentMemoryService — Phase 5.1

CRUD + search + versioning for PostgreSQL-backed persistent project memory.
Every operation is async. Optionally accepts an injected session for testing.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal

from memory.persistent_models import PersistentProjectMemory, PersistentMemoryVersion
from memory.persistent_schemas import (
    CategorySummary,
    MemoryCategory,
    PersistentMemoryResponse,
    PersistentMemoryVersionResponse,
)

logger = logging.getLogger(__name__)


class PersistentMemoryService:
    """PostgreSQL-backed persistent project memory service."""

    async def create_entry(
        self,
        project_id: int,
        category: MemoryCategory,
        content: str,
        agent_name: str = "system",
        metadata_json: Optional[Dict[str, Any]] = None,
        version: int = 1,
        session: Optional[AsyncSession] = None,
    ) -> PersistentMemoryResponse:
        """Create a memory entry."""
        async with session or AsyncSessionLocal() as ctx:
            entry = PersistentProjectMemory(
                project_id=project_id,
                category=category.value,
                agent_name=agent_name,
                content=content,
                metadata_json=metadata_json or {},
                version=version,
            )
            ctx.add(entry)
            await ctx.flush()

            version_rec = PersistentMemoryVersion(
                entry_id=entry.id,
                project_id=project_id,
                category=category.value,
                content=content,
                metadata_json=metadata_json or {},
                version=version,
                change_reason="Initial creation",
                changed_by=agent_name,
            )
            ctx.add(version_rec)
            await ctx.commit()
            await ctx.refresh(entry)

            logger.info("[PMEM] Created entry %d (category=%s) for project %d",
                        entry.id, category.value, project_id)
            return PersistentMemoryResponse.model_validate(entry)

    async def get_entry(
        self,
        project_id: int,
        entry_id: int,
        session: Optional[AsyncSession] = None,
    ) -> Optional[PersistentMemoryResponse]:
        """Get a single entry by ID."""
        async with session or AsyncSessionLocal() as ctx:
            result = await ctx.execute(
                select(PersistentProjectMemory).where(
                    PersistentProjectMemory.id == entry_id,
                    PersistentProjectMemory.project_id == project_id,
                    PersistentProjectMemory.is_active == True,
                )
            )
            entry = result.scalar_one_or_none()
            if not entry:
                return None
            return PersistentMemoryResponse.model_validate(entry)

    async def list_entries(
        self,
        project_id: int,
        category: Optional[MemoryCategory] = None,
        limit: int = 100,
        offset: int = 0,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryResponse]:
        """List entries, optionally filtered by category."""
        async with session or AsyncSessionLocal() as ctx:
            query = select(PersistentProjectMemory).where(
                PersistentProjectMemory.project_id == project_id,
                PersistentProjectMemory.is_active == True,
            )
            if category:
                query = query.where(PersistentProjectMemory.category == category.value)

            query = query.order_by(desc(PersistentProjectMemory.updated_at)).limit(limit).offset(offset)
            result = await ctx.execute(query)
            entries = result.scalars().all()
            return [PersistentMemoryResponse.model_validate(e) for e in entries]

    async def update_entry(
        self,
        project_id: int,
        entry_id: int,
        content: str,
        metadata_json: Optional[Dict[str, Any]] = None,
        change_reason: str = "",
        changed_by: str = "system",
        session: Optional[AsyncSession] = None,
    ) -> Optional[PersistentMemoryResponse]:
        """Update entry content and/or metadata (creates new version)."""
        async with session or AsyncSessionLocal() as ctx:
            result = await ctx.execute(
                select(PersistentProjectMemory).where(
                    PersistentProjectMemory.id == entry_id,
                    PersistentProjectMemory.project_id == project_id,
                    PersistentProjectMemory.is_active == True,
                )
            )
            entry = result.scalar_one_or_none()
            if not entry:
                return None

            new_version = entry.version + 1
            old_meta = dict(entry.metadata_json or {})

            entry.content = content
            entry.metadata_json = metadata_json if metadata_json is not None else old_meta
            entry.version = new_version
            entry.updated_at = datetime.now(timezone.utc)
            await ctx.flush()

            version_rec = PersistentMemoryVersion(
                entry_id=entry.id,
                project_id=project_id,
                category=entry.category,
                content=content,
                metadata_json=entry.metadata_json,
                version=new_version,
                change_reason=change_reason or "Updated",
                changed_by=changed_by,
            )
            ctx.add(version_rec)
            await ctx.commit()
            await ctx.refresh(entry)

            logger.info("[PMEM] Updated entry %d to v%d for project %d",
                        entry.id, new_version, project_id)
            return PersistentMemoryResponse.model_validate(entry)

    async def delete_entry(
        self,
        project_id: int,
        entry_id: int,
        session: Optional[AsyncSession] = None,
    ) -> bool:
        """Soft-delete a memory entry."""
        async with session or AsyncSessionLocal() as ctx:
            result = await ctx.execute(
                select(PersistentProjectMemory).where(
                    PersistentProjectMemory.id == entry_id,
                    PersistentProjectMemory.project_id == project_id,
                    PersistentProjectMemory.is_active == True,
                )
            )
            entry = result.scalar_one_or_none()
            if not entry:
                return False

            entry.is_active = False
            entry.updated_at = datetime.now(timezone.utc)
            await ctx.commit()

            logger.info("[PMEM] Soft-deleted entry %d for project %d", entry.id, project_id)
            return True

    async def search_entries(
        self,
        project_id: int,
        query: str,
        category: Optional[MemoryCategory] = None,
        limit: int = 50,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryResponse]:
        """Full-text search across entry content and agent names."""
        async with session or AsyncSessionLocal() as ctx:
            stmt = select(PersistentProjectMemory).where(
                PersistentProjectMemory.project_id == project_id,
                PersistentProjectMemory.is_active == True,
            )
            if category:
                stmt = stmt.where(PersistentProjectMemory.category == category.value)

            search_pattern = f"%{query}%"
            stmt = stmt.where(
                or_(
                    PersistentProjectMemory.content.ilike(search_pattern),
                    PersistentProjectMemory.agent_name.ilike(search_pattern),
                )
            )
            stmt = stmt.order_by(desc(PersistentProjectMemory.updated_at)).limit(limit)
            result = await ctx.execute(stmt)
            entries = result.scalars().all()
            return [PersistentMemoryResponse.model_validate(e) for e in entries]

    async def get_version_history(
        self,
        project_id: int,
        entry_id: int,
        limit: int = 50,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryVersionResponse]:
        """Get all versions of an entry, newest first."""
        async with session or AsyncSessionLocal() as ctx:
            stmt = (
                select(PersistentMemoryVersion)
                .where(
                    PersistentMemoryVersion.entry_id == entry_id,
                    PersistentMemoryVersion.project_id == project_id,
                )
                .order_by(desc(PersistentMemoryVersion.version))
                .limit(limit)
            )
            result = await ctx.execute(stmt)
            versions = result.scalars().all()
            return [PersistentMemoryVersionResponse.model_validate(v) for v in versions]

    async def get_category_summary(
        self,
        project_id: int,
        session: Optional[AsyncSession] = None,
    ) -> List[CategorySummary]:
        """Group counts by category."""
        async with session or AsyncSessionLocal() as ctx:
            stmt = (
                select(
                    PersistentProjectMemory.category,
                    func.count(PersistentProjectMemory.id),
                    func.max(PersistentProjectMemory.version),
                    func.max(PersistentProjectMemory.updated_at),
                )
                .where(
                    PersistentProjectMemory.project_id == project_id,
                    PersistentProjectMemory.is_active == True,
                )
                .group_by(PersistentProjectMemory.category)
            )
            result = await ctx.execute(stmt)
            summaries: List[CategorySummary] = []
            for row in result:
                summaries.append(CategorySummary(
                    category=row[0],
                    count=row[1],
                    latest_version=row[2] or 0,
                    last_updated=row[3],
                ))
            return summaries

    async def count_entries(
        self,
        project_id: int,
        category: Optional[MemoryCategory] = None,
        session: Optional[AsyncSession] = None,
    ) -> int:
        """Count active entries."""
        async with session or AsyncSessionLocal() as ctx:
            stmt = select(func.count(PersistentProjectMemory.id)).where(
                PersistentProjectMemory.project_id == project_id,
                PersistentProjectMemory.is_active == True,
            )
            if category:
                stmt = stmt.where(PersistentProjectMemory.category == category.value)
            result = await ctx.execute(stmt)
            return result.scalar() or 0
