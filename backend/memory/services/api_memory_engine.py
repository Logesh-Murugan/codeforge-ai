"""
APIMemoryEngine — Phase 5.1

Domain-specific memory engine for API endpoint definitions, request/response
schemas, authentication requirements, and versioning.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from memory.persistent_schemas import MemoryCategory, PersistentMemoryResponse
from memory.services.base_memory_service import BaseMemoryEngine

logger = logging.getLogger(__name__)


class APIMemoryEngine(BaseMemoryEngine):
    """Engine for API memory entries."""

    CATEGORY = MemoryCategory.API
    DOMAIN_FIELDS = [
        "endpoint", "method", "request_schema", "response_schema",
        "auth_required", "api_version", "rate_limit",
    ]

    async def get_by_endpoint(
        self,
        project_id: int,
        endpoint: str,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryResponse]:
        """Retrieve all entries for a specific API endpoint."""
        entries = await self.list_entries(project_id=project_id, session=session)
        return [
            e for e in entries
            if e.metadata_json.get("endpoint") == endpoint
        ]

    async def get_by_method(
        self,
        project_id: int,
        method: str,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryResponse]:
        """Retrieve entries filtered by HTTP method."""
        entries = await self.list_entries(project_id=project_id, session=session)
        return [
            e for e in entries
            if (e.metadata_json.get("method") or "").upper() == method.upper()
        ]

    async def get_api_catalog(
        self,
        project_id: int,
        session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Build a catalog of all API endpoints grouped by method."""
        entries = await self.list_entries(
            project_id=project_id, limit=500, session=session,
        )
        by_method: Dict[str, List[str]] = {}
        auth_endpoints: List[str] = []
        versions: set = set()

        for e in entries:
            meta = e.metadata_json
            method = (meta.get("method") or "UNKNOWN").upper()
            endpoint = meta.get("endpoint", "unknown")
            by_method.setdefault(method, []).append(endpoint)
            if meta.get("auth_required"):
                auth_endpoints.append(endpoint)
            ver = meta.get("api_version")
            if ver:
                versions.add(ver)

        return {
            "total": len(entries),
            "by_method": by_method,
            "authenticated_endpoints": auth_endpoints,
            "api_versions": sorted(versions),
        }
