"""
ContextRetrievalService — Phase 5.5

Context Retrieval System.
Optimized async multi-source retrieval for large projects.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import select

from app.db import AsyncSessionLocal
from context_engine.aggregators.context_aggregator import ContextAggregator
from context_engine.models.context_metadata import ContextMetadata
from context_engine.services.context_router_service import ContextRouterService

logger = logging.getLogger(__name__)


class ContextRetrievalService:
    """
    Context Retrieval System.
    """

    def __init__(self) -> None:
        self.aggregator = ContextAggregator()
        self.router = ContextRouterService()

    async def retrieve_context_bundle(
        self, project_id: int, target_agent: str
    ) -> Dict[str, Any]:
        """
        Fast async retrieval of aggregated & routed context bundle for `target_agent`.
        """
        master_bundle = await self.aggregator.aggregate_all_sources(project_id)
        routed_bundle = await self.router.route_context_for_agent(
            project_id=project_id, target_agent=target_agent, master_bundle=master_bundle
        )
        return routed_bundle

    async def list_project_contexts(self, project_id: int) -> List[Dict[str, Any]]:
        """List all context entities stored in DB for a project."""
        async with AsyncSessionLocal() as session:
            res = await session.execute(
                select(ContextMetadata)
                .where(ContextMetadata.project_id == project_id)
                .order_by(ContextMetadata.created_at)
            )
            rows = res.scalars().all()
            return [
                {
                    "id": row.id,
                    "project_id": row.project_id,
                    "context_type": row.context_type,
                    "version": row.version,
                    "producer_agent": row.producer_agent,
                    "status": row.status,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
                for row in rows
            ]
