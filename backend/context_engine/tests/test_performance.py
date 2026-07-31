"""
Performance Tests — Phase 5.5
"""
import time
import pytest
from unittest.mock import AsyncMock, patch
from context_engine.services.context_retrieval_service import ContextRetrievalService
from context_engine.orchestrators.context_orchestrator import ContextOrchestrator


@pytest.mark.asyncio
async def test_context_retrieval_performance():
    service = ContextRetrievalService()
    start = time.time()
    bundle = await service.retrieve_context_bundle(42, "backend_developer")
    elapsed = time.time() - start

    assert isinstance(bundle, dict)
    assert elapsed < 0.5  # Must complete under 500ms


@pytest.mark.asyncio
async def test_context_orchestrator_performance():
    orchestrator = ContextOrchestrator()
    with patch.object(orchestrator.history_manager, "log_event", new=AsyncMock()):
        start = time.time()
        res = await orchestrator.orchestrate_context_flow(42, "backend_developer")
        elapsed = time.time() - start

        assert res["project_id"] == 42
        assert elapsed < 0.5  # Must complete under 500ms
