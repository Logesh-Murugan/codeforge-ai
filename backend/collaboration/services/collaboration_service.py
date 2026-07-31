"""
CollaborationEngineService — Phase 5.4

Central orchestrator for the Agent Collaboration Engine.
Manages inter-agent message logging, context bundling, cross-validation, feedback loops,
and failure recovery.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.db import AsyncSessionLocal
from collaboration.models.collaboration_log import CollaborationLog
from collaboration.schemas.communication import (
    AgentMessageRequest,
    AgentMessageResponse,
    ContextBundleResponse,
)
from collaboration.schemas.validation import (
    CrossValidationRequest,
    CrossValidationResponse,
    FeedbackRequest,
    FeedbackResponse,
    UpdateFeedbackRequest,
)
from collaboration.services.analytics_service import AnalyticsService
from collaboration.services.context_exchange_service import ContextExchangeService
from collaboration.services.cross_validation_service import CrossValidationService

logger = logging.getLogger(__name__)


class CollaborationEngineService:
    """
    Unified facade service for the Agent Collaboration Engine.
    """

    def __init__(self) -> None:
        self.context_service = ContextExchangeService()
        self.validation_service = CrossValidationService()
        self.analytics_service = AnalyticsService()

    async def send_message(self, request: AgentMessageRequest) -> AgentMessageResponse:
        """
        Record an inter-agent message or context transfer in the database.
        """
        logger.info(
            f"[COLLABORATION-SERVICE] Message from '{request.sender_agent}' to '{request.receiver_agent}' (pattern={request.pattern.value})"
        )

        async with AsyncSessionLocal() as session:
            log_entry = CollaborationLog(
                project_id=request.project_id,
                sender_agent=request.sender_agent,
                receiver_agent=request.receiver_agent,
                pattern=request.pattern.value,
                payload_json=request.payload,
                status="sent",
            )
            session.add(log_entry)
            await session.commit()
            await session.refresh(log_entry)

            return AgentMessageResponse(
                log_id=log_entry.id,
                project_id=log_entry.project_id,
                sender_agent=log_entry.sender_agent,
                receiver_agent=log_entry.receiver_agent,
                pattern=log_entry.pattern,
                status=log_entry.status,
                created_at=log_entry.created_at,
            )

    async def get_context_bundle(
        self, project_id: int, target_agent: str
    ) -> ContextBundleResponse:
        """
        Assemble multi-agent context bundle for `target_agent`.
        """
        return await self.context_service.assemble_context_bundle(
            project_id, target_agent
        )

    async def validate_cross_agent(
        self, request: CrossValidationRequest
    ) -> CrossValidationResponse:
        """
        Run cross-agent validation check.
        """
        return await self.validation_service.validate_output(request)

    async def submit_feedback(self, request: FeedbackRequest) -> FeedbackResponse:
        """
        Record cross-agent feedback entry.
        """
        logger.info(
            f"[COLLABORATION-SERVICE] Feedback from '{request.from_agent}' to '{request.to_agent}': {request.comments[:60]}"
        )

        async with AsyncSessionLocal() as session:
            log_entry = CollaborationLog(
                project_id=request.project_id,
                sender_agent=request.from_agent,
                receiver_agent=request.to_agent,
                pattern="feedback",
                payload_json={
                    "feedback_type": request.feedback_type,
                    "comments": request.comments,
                    "suggested_changes": request.suggested_changes,
                },
                status="open",
            )
            session.add(log_entry)
            await session.commit()
            await session.refresh(log_entry)

            return FeedbackResponse(
                feedback_id=log_entry.id,
                project_id=log_entry.project_id,
                from_agent=log_entry.sender_agent,
                to_agent=log_entry.receiver_agent,
                status="open",
                created_at=log_entry.created_at,
            )

    async def update_feedback_status(
        self, feedback_id: int, request: UpdateFeedbackRequest
    ) -> FeedbackResponse:
        """
        Update the status of a feedback entry (open -> resolved/ignored).
        """
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            res = await session.execute(
                select(CollaborationLog).where(CollaborationLog.id == feedback_id)
            )
            entry = res.scalar_one_or_none()
            if not entry:
                raise ValueError(f"Feedback entry {feedback_id} not found.")

            entry.status = request.status
            if request.resolution_notes:
                payload = dict(entry.payload_json or {})
                payload["resolution_notes"] = request.resolution_notes
                entry.payload_json = payload

            await session.commit()
            await session.refresh(entry)

            return FeedbackResponse(
                feedback_id=entry.id,
                project_id=entry.project_id,
                from_agent=entry.sender_agent,
                to_agent=entry.receiver_agent,
                status=entry.status,
                created_at=entry.created_at,
            )

    async def get_collaboration_history(self, project_id: int) -> List[Dict[str, Any]]:
        """
        Fetch execution trace and inter-agent message logs for a project.
        """
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            res = await session.execute(
                select(CollaborationLog)
                .where(CollaborationLog.project_id == project_id)
                .order_by(CollaborationLog.created_at)
            )
            logs = res.scalars().all()
            return [
                {
                    "id": log.id,
                    "project_id": log.project_id,
                    "sender_agent": log.sender_agent,
                    "receiver_agent": log.receiver_agent,
                    "pattern": log.pattern,
                    "payload": log.payload_json,
                    "status": log.status,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
                for log in logs
            ]

    async def get_feedback_history(self, project_id: int) -> List[FeedbackResponse]:
        """
        Fetch all feedback entries for a project.
        """
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            res = await session.execute(
                select(CollaborationLog)
                .where(
                    CollaborationLog.project_id == project_id,
                    CollaborationLog.pattern == "feedback",
                )
                .order_by(CollaborationLog.created_at)
            )
            logs = res.scalars().all()
            return [
                FeedbackResponse(
                    feedback_id=log.id,
                    project_id=log.project_id,
                    from_agent=log.sender_agent,
                    to_agent=log.receiver_agent,
                    status=log.status,
                    created_at=log.created_at,
                )
                for log in logs
            ]
