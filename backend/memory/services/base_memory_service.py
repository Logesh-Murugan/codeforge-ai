"""
BaseMemoryEngine — Phase 5.1

Abstract base class for all domain-specific memory engines.

Provides generic CRUD, search, version history, and similarity retrieval
by delegating to the existing ``PersistentMemoryService`` (PostgreSQL)
and ``MemoryService`` (ChromaDB vectors).

Subclasses set ``CATEGORY`` and ``DOMAIN_FIELDS`` and optionally override
the ``_pre_create``, ``_post_create``, ``_pre_update`` hooks for
domain-specific validation or enrichment.
"""
from __future__ import annotations

import logging
from abc import ABC
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from memory.persistent_schemas import (
    MemoryCategory,
    PersistentMemoryResponse,
    PersistentMemoryVersionResponse,
)
from memory.persistent_service import PersistentMemoryService
from memory.utils.memory_helpers import (
    inject_domain_fields,
    extract_domain_fields,
    merge_metadata,
    sanitize_content,
)

logger = logging.getLogger(__name__)


class BaseMemoryEngine(ABC):
    """
    Abstract base for all 12 domain-specific memory engines.

    Each subclass must set:
        CATEGORY       — the ``MemoryCategory`` this engine owns.
        DOMAIN_FIELDS  — list of domain-specific field names stored in
                         ``metadata_json``.

    Lifecycle hooks (override in subclasses as needed):
        _pre_create(content, metadata, domain_fields) → (content, metadata)
        _post_create(entry) → None
        _pre_update(content, metadata, domain_fields) → (content, metadata)
    """

    CATEGORY: MemoryCategory
    DOMAIN_FIELDS: List[str] = []

    def __init__(
        self,
        persistent_service: Optional[PersistentMemoryService] = None,
    ) -> None:
        self._psvc = persistent_service or PersistentMemoryService()
        logger.info(
            "[%s] Engine initialised (category=%s)",
            self.__class__.__name__,
            self.CATEGORY.value,
        )

    # ──────────────────────────────────────────────────────────────────────
    # Lifecycle hooks — override in subclasses
    # ──────────────────────────────────────────────────────────────────────

    def _pre_create(
        self,
        content: str,
        metadata: Dict[str, Any],
        domain_fields: Dict[str, Any],
    ) -> tuple[str, Dict[str, Any]]:
        """
        Called before creating an entry.  Return possibly modified
        (content, metadata) tuple.  Override for domain validation.
        """
        return content, metadata

    def _post_create(self, entry: PersistentMemoryResponse) -> None:
        """Called after an entry is successfully created."""

    def _pre_update(
        self,
        content: str,
        metadata: Dict[str, Any],
        domain_fields: Dict[str, Any],
    ) -> tuple[str, Dict[str, Any]]:
        """Called before updating an entry.  Same contract as _pre_create."""
        return content, metadata

    # ──────────────────────────────────────────────────────────────────────
    # CRUD
    # ──────────────────────────────────────────────────────────────────────

    async def create(
        self,
        project_id: int,
        content: str,
        agent_name: str = "system",
        metadata_json: Optional[Dict[str, Any]] = None,
        domain_fields: Optional[Dict[str, Any]] = None,
        version: int = 1,
        session: Optional[AsyncSession] = None,
    ) -> PersistentMemoryResponse:
        """Create a new memory entry in this engine's category."""
        meta = metadata_json or {}
        dfields = domain_fields or {}
        meta = inject_domain_fields(meta, dfields)

        content = sanitize_content(content)
        content, meta = self._pre_create(content, meta, dfields)

        entry = await self._psvc.create_entry(
            project_id=project_id,
            category=self.CATEGORY,
            content=content,
            agent_name=agent_name,
            metadata_json=meta,
            version=version,
            session=session,
        )
        self._post_create(entry)
        logger.info(
            "[%s] Created entry %d for project %d",
            self.__class__.__name__, entry.id, project_id,
        )
        return entry

    async def get(
        self,
        project_id: int,
        entry_id: int,
        session: Optional[AsyncSession] = None,
    ) -> Optional[PersistentMemoryResponse]:
        """Retrieve a single entry by ID, scoped to this engine's category."""
        entry = await self._psvc.get_entry(
            project_id=project_id,
            entry_id=entry_id,
            session=session,
        )
        if entry and entry.category != self.CATEGORY.value:
            return None  # Entry exists but belongs to a different category
        return entry

    async def list_entries(
        self,
        project_id: int,
        limit: int = 100,
        offset: int = 0,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryResponse]:
        """List all active entries for this engine's category."""
        return await self._psvc.list_entries(
            project_id=project_id,
            category=self.CATEGORY,
            limit=limit,
            offset=offset,
            session=session,
        )

    async def update(
        self,
        project_id: int,
        entry_id: int,
        content: str,
        metadata_json: Optional[Dict[str, Any]] = None,
        domain_fields: Optional[Dict[str, Any]] = None,
        change_reason: str = "",
        changed_by: str = "system",
        session: Optional[AsyncSession] = None,
    ) -> Optional[PersistentMemoryResponse]:
        """Update an entry, creating a new version."""
        # Verify the entry belongs to this category
        existing = await self.get(project_id, entry_id, session=session)
        if existing is None:
            return None

        meta = metadata_json if metadata_json is not None else dict(existing.metadata_json)
        dfields = domain_fields or {}
        meta = inject_domain_fields(meta, dfields)

        content = sanitize_content(content)
        content, meta = self._pre_update(content, meta, dfields)

        return await self._psvc.update_entry(
            project_id=project_id,
            entry_id=entry_id,
            content=content,
            metadata_json=meta,
            change_reason=change_reason,
            changed_by=changed_by,
            session=session,
        )

    async def delete(
        self,
        project_id: int,
        entry_id: int,
        session: Optional[AsyncSession] = None,
    ) -> bool:
        """Soft-delete an entry (only if it belongs to this category)."""
        existing = await self.get(project_id, entry_id, session=session)
        if existing is None:
            return False
        return await self._psvc.delete_entry(
            project_id=project_id,
            entry_id=entry_id,
            session=session,
        )

    # ──────────────────────────────────────────────────────────────────────
    # Search
    # ──────────────────────────────────────────────────────────────────────

    async def search(
        self,
        project_id: int,
        query: str,
        limit: int = 50,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryResponse]:
        """Full-text search scoped to this engine's category."""
        return await self._psvc.search_entries(
            project_id=project_id,
            query=query,
            category=self.CATEGORY,
            limit=limit,
            session=session,
        )

    # ──────────────────────────────────────────────────────────────────────
    # Version history
    # ──────────────────────────────────────────────────────────────────────

    async def get_versions(
        self,
        project_id: int,
        entry_id: int,
        limit: int = 50,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryVersionResponse]:
        """Get version history for an entry in this category."""
        existing = await self.get(project_id, entry_id, session=session)
        if existing is None:
            return []
        return await self._psvc.get_version_history(
            project_id=project_id,
            entry_id=entry_id,
            limit=limit,
            session=session,
        )

    # ──────────────────────────────────────────────────────────────────────
    # Similarity retrieval (ChromaDB)
    # ──────────────────────────────────────────────────────────────────────

    async def find_similar(
        self,
        project_id: int,
        query: str,
        limit: int = 5,
        threshold: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Semantic similarity search via the ChromaDB-backed MemoryService.

        Falls back gracefully if the vector service is not available.
        """
        try:
            from memory.manager import default_manager
            svc = default_manager.get_service()
            collection = self.CATEGORY.value
            results = svc.retrieve_memory(
                project_id=project_id,
                collection_name=collection,
                query=query,
                limit=limit,
                threshold=threshold,
            )
            return results
        except Exception as exc:
            logger.warning(
                "[%s] Similarity search unavailable: %s",
                self.__class__.__name__, exc,
            )
            return []

    # ──────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────

    def enrich_response(
        self,
        entry: PersistentMemoryResponse,
    ) -> Dict[str, Any]:
        """
        Convert a PersistentMemoryResponse to a dict with domain-specific
        fields extracted from metadata_json.
        """
        data = entry.model_dump()
        extracted = extract_domain_fields(
            data.get("metadata_json", {}),
            self.DOMAIN_FIELDS,
        )
        data.update(extracted)
        return data

    async def count(
        self,
        project_id: int,
        session: Optional[AsyncSession] = None,
    ) -> int:
        """Count active entries for this category."""
        return await self._psvc.count_entries(
            project_id=project_id,
            category=self.CATEGORY,
            session=session,
        )
