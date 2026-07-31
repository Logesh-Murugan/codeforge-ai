"""
DeploymentMemoryEngine — Phase 5.1

Domain-specific memory engine for deployment configurations,
environments, providers, and health checks.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from memory.persistent_schemas import MemoryCategory, PersistentMemoryResponse
from memory.services.base_memory_service import BaseMemoryEngine

logger = logging.getLogger(__name__)


class DeploymentMemoryEngine(BaseMemoryEngine):
    """Engine for deployment memory entries."""

    CATEGORY = MemoryCategory.DEPLOYMENT
    DOMAIN_FIELDS = [
        "environment", "provider", "config_type", "status",
        "deploy_url", "build_command", "env_variables", "health_check_url",
    ]

    async def get_by_environment(
        self,
        project_id: int,
        environment: str,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryResponse]:
        """Retrieve entries for a specific environment (dev/staging/production)."""
        entries = await self.list_entries(project_id=project_id, session=session)
        return [
            e for e in entries
            if e.metadata_json.get("environment") == environment
        ]

    async def get_by_provider(
        self,
        project_id: int,
        provider: str,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryResponse]:
        """Retrieve entries filtered by cloud provider."""
        entries = await self.list_entries(project_id=project_id, session=session)
        return [
            e for e in entries
            if (e.metadata_json.get("provider") or "").lower() == provider.lower()
        ]

    async def get_by_status(
        self,
        project_id: int,
        status: str,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryResponse]:
        """Retrieve entries filtered by deployment status."""
        entries = await self.list_entries(project_id=project_id, session=session)
        return [
            e for e in entries
            if e.metadata_json.get("status") == status
        ]

    async def get_deployment_overview(
        self,
        project_id: int,
        session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Build an overview of all deployment configurations."""
        entries = await self.list_entries(
            project_id=project_id, limit=500, session=session,
        )
        by_env: Dict[str, int] = {}
        by_provider: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        urls: List[str] = []
        all_env_vars: set = set()

        for e in entries:
            meta = e.metadata_json
            env = meta.get("environment", "unspecified")
            by_env[env] = by_env.get(env, 0) + 1
            prov = meta.get("provider")
            if prov:
                by_provider[prov] = by_provider.get(prov, 0) + 1
            st = meta.get("status", "unknown")
            by_status[st] = by_status.get(st, 0) + 1
            url = meta.get("deploy_url")
            if url:
                urls.append(url)
            for ev in meta.get("env_variables", []) or []:
                all_env_vars.add(ev)

        return {
            "total": len(entries),
            "by_environment": by_env,
            "by_provider": by_provider,
            "by_status": by_status,
            "deploy_urls": urls,
            "required_env_variables": sorted(all_env_vars),
        }
