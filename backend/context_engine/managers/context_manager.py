"""
ContextManager — Phase 5.5

Context Manager system for context creation, versioning, storage, and retrieval.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import select

from app.db import AsyncSessionLocal
from context_engine.models.context_metadata import ContextMetadata
from context_engine.schemas.context_payload import ContextCreateRequest, ContextEntityResponse

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Context Manager.
    """

    async def create_or_update_context(
        self, request: ContextCreateRequest
    ) -> ContextEntityResponse:
        """
        Store a new context version or update existing context entity.
        """
        async with AsyncSessionLocal() as session:
            # Check for existing context of this type
            res = await session.execute(
                select(ContextMetadata).where(
                    ContextMetadata.project_id == request.project_id,
                    ContextMetadata.context_type == request.context_type.value,
                )
            )
            existing = res.scalar_one_or_none()

            if existing:
                existing.version += 1
                existing.payload_json = request.payload
                existing.producer_agent = request.producer_agent
                await session.commit()
                await session.refresh(existing)
                entity = existing
            else:
                entity = ContextMetadata(
                    project_id=request.project_id,
                    context_type=request.context_type.value,
                    version=1,
                    producer_agent=request.producer_agent,
                    payload_json=request.payload,
                    status="valid",
                )
                session.add(entity)
                await session.commit()
                await session.refresh(entity)

            return ContextEntityResponse(
                id=entity.id,
                project_id=entity.project_id,
                context_type=entity.context_type,
                version=entity.version,
                producer_agent=entity.producer_agent,
                payload=entity.payload_json or {},
                status=entity.status,
                created_at=entity.created_at,
                updated_at=entity.updated_at,
            )

    async def get_context(self, context_id: int) -> Optional[ContextEntityResponse]:
        """Retrieve a specific context entity by ID."""
        async with AsyncSessionLocal() as session:
            res = await session.execute(
                select(ContextMetadata).where(ContextMetadata.id == context_id)
            )
            entity = res.scalar_one_or_none()
            if not entity:
                return None

            return ContextEntityResponse(
                id=entity.id,
                project_id=entity.project_id,
                context_type=entity.context_type,
                version=entity.version,
                producer_agent=entity.producer_agent,
                payload=entity.payload_json or {},
                status=entity.status,
                created_at=entity.created_at,
                updated_at=entity.updated_at,
            )

    async def invalidate_context(self, context_id: int) -> bool:
        """Soft-delete or mark a context entity as invalid."""
        async with AsyncSessionLocal() as session:
            res = await session.execute(
                select(ContextMetadata).where(ContextMetadata.id == context_id)
            )
            entity = res.scalar_one_or_none()
            if not entity:
                return False

            entity.status = "invalid"
            await session.commit()
            return True
