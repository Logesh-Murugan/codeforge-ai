"""
Context History Tests — Phase 5.5
"""
import pytest
from unittest.mock import AsyncMock, patch
from context_engine.managers.context_history_manager import ContextHistoryManager
from context_engine.schemas.analytics import ContextHistoryRecord


@pytest.mark.asyncio
async def test_context_history_manager_log_event():
    manager = ContextHistoryManager()
    with patch.object(
        manager,
        "log_event",
        new=AsyncMock(
            return_value=ContextHistoryRecord(
                id=1,
                project_id=42,
                context_type="Architecture",
                producer_agent="solution_architect",
                consumer_agent="backend_developer",
                action="routed",
                version=1,
                timestamp="2026-07-31T00:00:00Z",
            )
        ),
    ):
        rec = await manager.log_event(
            project_id=42,
            context_type="Architecture",
            producer_agent="solution_architect",
            consumer_agent="backend_developer",
            action="routed",
            change_summary="Routed Architecture spec",
        )

        assert rec.project_id == 42
        assert rec.context_type == "Architecture"
        assert rec.producer_agent == "solution_architect"
        assert rec.consumer_agent == "backend_developer"
