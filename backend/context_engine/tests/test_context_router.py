"""
Context Routing Tests — Phase 5.5
"""
import pytest
from context_engine.services.context_router_service import ContextRouterService


@pytest.mark.asyncio
async def test_route_context_for_business_analyst():
    router = ContextRouterService()
    master = {
        "Project": {"id": 42},
        "Memory": {"history": []},
        "Human Approval": {"status": "approved"},
        "RAG": {"text": "rag"},
        "Requirement": {"reqs": "spec"},
        "Database": {"tables": []},  # Should NOT be routed to BA
    }

    routed = await router.route_context_for_agent(42, "business_analyst", master)
    assert "Project" in routed
    assert "Memory" in routed
    assert "Human Approval" in routed
    assert "RAG" in routed
    assert "Database" not in routed


@pytest.mark.asyncio
async def test_route_context_for_backend_developer():
    router = ContextRouterService()
    master = {
        "Architecture": {"arch": "microservices"},
        "API": {"spec": "REST"},
        "Database": {"tables": ["users"]},
        "Security": {"auth": "JWT"},
        "Testing": {"qa": "pytest"},
        "Memory": {"history": []},
        "RAG": {"text": "context"},
        "Backend": {"code": "py"},
        "Frontend": {"ui": "react"},  # Should NOT be routed to Backend
    }

    routed = await router.route_context_for_agent(42, "backend_developer", master)
    assert "Architecture" in routed
    assert "API" in routed
    assert "Database" in routed
    assert "Security" in routed
    assert "Frontend" not in routed
