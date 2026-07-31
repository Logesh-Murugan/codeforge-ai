"""
AgentMemoryEngine — Phase 5.1

Domain-specific memory engine for agent execution outputs, tracking
which agent produced what, with what model, and how long it took.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from memory.persistent_schemas import MemoryCategory, PersistentMemoryResponse
from memory.services.base_memory_service import BaseMemoryEngine

logger = logging.getLogger(__name__)


class AgentMemoryEngine(BaseMemoryEngine):
    """Engine for agent-specific memory entries."""

    CATEGORY = MemoryCategory.AGENT
    DOMAIN_FIELDS = [
        "agent_type", "task_context", "output_summary",
        "model_used", "execution_duration_ms", "token_count",
    ]

    async def get_by_agent(
        self,
        project_id: int,
        agent_name: str,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryResponse]:
        """Retrieve all entries produced by a specific agent."""
        entries = await self.list_entries(project_id=project_id, session=session)
        return [e for e in entries if e.agent_name == agent_name]

    async def get_by_agent_type(
        self,
        project_id: int,
        agent_type: str,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryResponse]:
        """Retrieve all entries for a specific agent type."""
        entries = await self.list_entries(project_id=project_id, session=session)
        return [
            e for e in entries
            if e.metadata_json.get("agent_type") == agent_type
        ]

    async def get_execution_stats(
        self,
        project_id: int,
        session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """
        Aggregate execution statistics across all agents for a project.
        """
        entries = await self.list_entries(
            project_id=project_id, limit=500, session=session,
        )
        total_tokens = 0
        total_duration = 0.0
        agent_counts: Dict[str, int] = {}
        for e in entries:
            meta = e.metadata_json
            total_tokens += meta.get("token_count", 0) or 0
            total_duration += meta.get("execution_duration_ms", 0) or 0
            agent_counts[e.agent_name] = agent_counts.get(e.agent_name, 0) + 1

        return {
            "total_entries": len(entries),
            "total_tokens": total_tokens,
            "total_duration_ms": total_duration,
            "agents": agent_counts,
        }
