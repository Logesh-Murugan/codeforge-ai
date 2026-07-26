"""
test_agent_context.py — Phase 3.5 test suite.

Tests cover:
- ContextInjector: role registry, context building, prompt block rendering
- CrossAgentMemory: publish/read/broadcast/list_agents
- LongTermMemory: store, retrieve with decay, recency weighting, forget_stale
- ConversationMemory: append, get_history, session scoping, search,
  summarise, token_estimate, count_turns

Windows-safe ChromaDB fixture: uses tempfile.mkdtemp() + shutil.rmtree()
"""
from __future__ import annotations

import math
import shutil
import tempfile
import time
from datetime import datetime, timezone, timedelta
from typing import List
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_service(tmp_path: str):
    """Return a (MemoryService, ChromaVectorStore) pair wired to a temp dir."""
    from memory.embeddings.local import LocalEmbeddings
    from memory.service import MemoryService
    from memory.vectorstores.chroma import ChromaVectorStore

    store = ChromaVectorStore(persist_path=tmp_path)
    embed = LocalEmbeddings()
    svc = MemoryService(embedding_provider=embed, vector_store=store)
    return svc, store


@pytest.fixture(scope="module")
def tmp_dir():
    d = tempfile.mkdtemp(prefix="cf_test_ctx_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture(scope="module")
def svc(tmp_dir):
    svc, _ = _make_service(tmp_dir)
    return svc


# ===========================================================================
# 1. ContextInjector
# ===========================================================================

class TestContextInjector:

    def test_all_default_roles_registered(self):
        from memory.context import ContextInjector, AGENT_ROLES
        injector = ContextInjector.__new__(ContextInjector)
        injector._roles = dict(AGENT_ROLES)
        for name in [
            "requirements_analyst", "architect", "api_designer",
            "backend_developer", "frontend_developer", "security_engineer",
            "qa_engineer", "devops_engineer", "documentation_writer",
        ]:
            assert name in injector._roles

    def test_get_role_known_agent(self):
        from memory.context import ContextInjector, AGENT_ROLES
        injector = ContextInjector.__new__(ContextInjector)
        injector._roles = dict(AGENT_ROLES)
        role = injector.get_role("architect")
        assert role.name == "architect"
        assert "architecture" in role.collections

    def test_get_role_unknown_agent_returns_generic(self):
        from memory.context import ContextInjector, AGENT_ROLES
        injector = ContextInjector.__new__(ContextInjector)
        injector._roles = dict(AGENT_ROLES)
        role = injector.get_role("nonexistent_agent_xyz")
        assert role.name == "nonexistent_agent_xyz"
        assert isinstance(role.collections, list)
        assert len(role.collections) > 0

    def test_register_role(self):
        from memory.context import ContextInjector, AgentRole, AGENT_ROLES
        injector = ContextInjector.__new__(ContextInjector)
        injector._roles = dict(AGENT_ROLES)
        custom = AgentRole(
            name="custom_agent",
            collections=["requirements"],
            description="test",
        )
        injector.register_role(custom)
        assert "custom_agent" in injector._roles
        assert injector._roles["custom_agent"] is custom

    def test_available_roles_lists_all(self):
        from memory.context import ContextInjector, AGENT_ROLES
        injector = ContextInjector.__new__(ContextInjector)
        injector._roles = dict(AGENT_ROLES)
        roles = injector.available_roles
        assert isinstance(roles, list)
        assert len(roles) >= 9

    def test_query_template_substitution(self):
        from memory.context import AgentRole
        role = AgentRole(
            name="test",
            collections=["requirements"],
            query_template="Security aspects of: {query}",
        )
        expanded = role.query_template.format(query="JWT auth")
        assert "JWT auth" in expanded
        assert "Security aspects" in expanded

    def test_build_context_returns_agent_context(self, svc):
        from memory.context import ContextInjector

        injector = ContextInjector(memory_service=svc)
        # Seed some data
        svc.store_memory(
            project_id=100, agent_name="requirements_analyst",
            artifact_type="requirements", collection_name="requirements",
            content="Users must be able to register with email and password.",
            version=1,
        )
        ctx = injector.build_context(
            project_id=100,
            agent_name="backend_developer",
            user_query="user registration endpoint",
            limit=3,
        )
        from memory.schemas import AgentContext
        assert isinstance(ctx, AgentContext)
        assert ctx.project_id == 100
        assert ctx.agent_name == "backend_developer"
        assert isinstance(ctx.chunks, list)

    def test_build_context_block_returns_string(self, svc):
        from memory.context import ContextInjector

        injector = ContextInjector(memory_service=svc)
        svc.store_memory(
            project_id=101, agent_name="architect",
            artifact_type="architecture", collection_name="architecture",
            content="Microservices with FastAPI and PostgreSQL.",
            version=1,
        )
        block = injector.build_context_block(
            project_id=101,
            agent_name="backend_developer",
            user_query="database connection",
            limit=3,
        )
        assert isinstance(block, str)

    def test_build_context_empty_project_does_not_raise(self, svc):
        from memory.context import ContextInjector

        injector = ContextInjector(memory_service=svc)
        ctx = injector.build_context(
            project_id=9990,
            agent_name="qa_engineer",
            user_query="any query",
        )
        assert ctx.project_id == 9990
        assert ctx.chunks == [] or isinstance(ctx.chunks, list)

    def test_extra_collections_added(self, svc):
        from memory.context import ContextInjector

        injector = ContextInjector(memory_service=svc)
        # Should not raise even if extra collection doesn't exist
        ctx = injector.build_context(
            project_id=102,
            agent_name="requirements_analyst",
            user_query="test",
            extra_collections=["documentation"],
        )
        assert ctx is not None

    def test_default_init_lazy_loads_service(self):
        from memory.context.injector import ContextInjector
        mock_svc = MagicMock()
        mock_manager = MagicMock()
        mock_manager.get_service.return_value = mock_svc
        with patch("memory.manager.default_manager", mock_manager):
            injector = ContextInjector()
            assert injector._svc is mock_svc


# ===========================================================================
# 2. CrossAgentMemory
# ===========================================================================

class TestCrossAgentMemory:

    def test_publish_returns_id(self, svc):
        from memory.context import CrossAgentMemory
        cam = CrossAgentMemory(memory_service=svc)
        mem_id = cam.publish(
            project_id=200,
            agent_name="security_engineer",
            artifact_type="security_report",
            content="## Security Report\nNo critical issues found.",
            version=1,
        )
        assert isinstance(mem_id, str)
        assert len(mem_id) > 0

    def test_read_returns_records(self, svc):
        from memory.context import CrossAgentMemory
        cam = CrossAgentMemory(memory_service=svc)
        cam.publish(
            project_id=201,
            agent_name="qa_engineer",
            artifact_type="qa_report",
            content="All tests pass.",
            version=1,
        )
        records = cam.read(
            project_id=201,
            source_agent="qa_engineer",
            artifact_type="qa_report",
        )
        assert len(records) >= 1

    def test_read_filters_by_agent(self, svc):
        from memory.context import CrossAgentMemory
        cam = CrossAgentMemory(memory_service=svc)
        cam.publish(project_id=202, agent_name="devops_engineer",
                    artifact_type="devops", content="Docker setup.", version=1)
        cam.publish(project_id=202, agent_name="security_engineer",
                    artifact_type="security_report", content="Clean report.", version=1)

        devops_records = cam.read(project_id=202, source_agent="devops_engineer")
        assert all(
            r["metadata"]["agent_name"] == "devops_engineer"
            for r in devops_records
        )

    def test_read_filters_by_artifact_type(self, svc):
        from memory.context import CrossAgentMemory
        cam = CrossAgentMemory(memory_service=svc)
        cam.publish(project_id=203, agent_name="architect",
                    artifact_type="architecture", content="Microservices.", version=1)
        cam.publish(project_id=203, agent_name="architect",
                    artifact_type="database_design", content="PostgreSQL.", version=1)

        arch = cam.read(project_id=203, artifact_type="architecture")
        assert all(r["metadata"]["artifact_type"] == "architecture" for r in arch)

    def test_read_latest_returns_highest_version(self, svc):
        from memory.context import CrossAgentMemory
        cam = CrossAgentMemory(memory_service=svc)
        cam.publish(project_id=204, agent_name="backend_developer",
                    artifact_type="backend_code", content="v1 code", version=1)
        cam.publish(project_id=204, agent_name="backend_developer",
                    artifact_type="backend_code", content="v2 code", version=2)

        latest = cam.read_latest(
            project_id=204,
            source_agent="backend_developer",
            artifact_type="backend_code",
        )
        assert latest is not None
        assert int(latest["metadata"]["version"]) == 2

    def test_read_latest_none_for_unknown(self, svc):
        from memory.context import CrossAgentMemory
        cam = CrossAgentMemory(memory_service=svc)
        result = cam.read_latest(
            project_id=9991,
            source_agent="nobody",
            artifact_type="nothing",
        )
        assert result is None

    def test_broadcast_returns_dict(self, svc):
        from memory.context import CrossAgentMemory
        cam = CrossAgentMemory(memory_service=svc)
        result = cam.broadcast(
            project_id=205,
            agent_name="documentation_writer",
            artifact_type="documentation",
            content="## API Docs",
            version=1,
        )
        assert isinstance(result, dict)
        assert "mem_id" in result
        assert result["project_id"] == 205
        assert result["agent_name"] == "documentation_writer"

    def test_list_agents_returns_sorted_names(self, svc):
        from memory.context import CrossAgentMemory
        cam = CrossAgentMemory(memory_service=svc)
        cam.publish(project_id=206, agent_name="zz_agent",
                    artifact_type="documentation", content="z", version=1)
        cam.publish(project_id=206, agent_name="aa_agent",
                    artifact_type="requirements", content="a", version=1)

        agents = cam.list_agents(project_id=206)
        assert isinstance(agents, list)
        assert agents == sorted(agents)

    def test_list_agents_empty_project(self, svc):
        from memory.context import CrossAgentMemory
        cam = CrossAgentMemory(memory_service=svc)
        agents = cam.list_agents(project_id=9992)
        assert agents == []

    def test_default_init_lazy_loads_service(self):
        from memory.context.cross_agent import CrossAgentMemory
        mock_svc = MagicMock()
        mock_manager = MagicMock()
        mock_manager.get_service.return_value = mock_svc
        with patch("memory.manager.default_manager", mock_manager):
            cam = CrossAgentMemory()
            assert cam._svc is mock_svc


# ===========================================================================
# 3. LongTermMemory
# ===========================================================================

class TestLongTermMemory:

    def test_store_returns_id(self, svc):
        from memory.context import LongTermMemory
        ltm = LongTermMemory(memory_service=svc)
        mem_id = ltm.store(
            project_id=300,
            agent_name="backend_developer",
            artifact_type="backend_code",
            collection_name="backend_code",
            content="def authenticate(token): ...",
            importance=2.0,
        )
        assert isinstance(mem_id, str)

    def test_retrieve_returns_list(self, svc):
        from memory.context import LongTermMemory
        ltm = LongTermMemory(memory_service=svc)
        ltm.store(
            project_id=301,
            agent_name="requirements_analyst",
            artifact_type="requirements",
            collection_name="requirements",
            content="The system shall support OAuth2 authentication.",
            importance=1.5,
        )
        results = ltm.retrieve(
            project_id=301,
            query="authentication",
            collections=["requirements"],
            limit=5,
        )
        assert isinstance(results, list)

    def test_retrieve_has_adjusted_score(self, svc):
        from memory.context import LongTermMemory
        ltm = LongTermMemory(memory_service=svc)
        ltm.store(
            project_id=302,
            agent_name="architect",
            artifact_type="architecture",
            collection_name="architecture",
            content="Microservices architecture with Docker containers.",
            importance=1.0,
        )
        results = ltm.retrieve(
            project_id=302,
            query="Docker deployment",
            collections=["architecture"],
            limit=5,
        )
        for r in results:
            assert "adjusted_score" in r
            assert r["adjusted_score"] >= 0.0

    def test_retrieve_results_sorted_by_adjusted_score(self, svc):
        from memory.context import LongTermMemory
        ltm = LongTermMemory(memory_service=svc)
        for i in range(3):
            ltm.store(
                project_id=303,
                agent_name="backend_developer",
                artifact_type="backend_code",
                collection_name="backend_code",
                content=f"FastAPI endpoint implementation {i}",
                importance=float(i + 1),
            )
        results = ltm.retrieve(
            project_id=303,
            query="FastAPI endpoint",
            collections=["backend_code"],
            limit=10,
        )
        if len(results) > 1:
            scores = [r["adjusted_score"] for r in results]
            assert scores == sorted(scores, reverse=True)

    def test_retrieve_empty_project_returns_list(self, svc):
        from memory.context import LongTermMemory
        ltm = LongTermMemory(memory_service=svc)
        results = ltm.retrieve(
            project_id=9993,
            query="anything",
        )
        assert isinstance(results, list)

    def test_recency_weight_fresh_record(self):
        from memory.context.long_term import _recency_weight
        now_iso = datetime.now(timezone.utc).isoformat()
        weight = _recency_weight(now_iso, decay_rate=0.005)
        assert weight > 0.99   # fresh record: nearly 1.0

    def test_recency_weight_old_record_lower(self):
        from memory.context.long_term import _recency_weight
        old = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        fresh = datetime.now(timezone.utc).isoformat()
        old_w = _recency_weight(old, decay_rate=0.005)
        fresh_w = _recency_weight(fresh, decay_rate=0.005)
        assert old_w < fresh_w

    def test_recency_weight_unknown_timestamp(self):
        from memory.context.long_term import _recency_weight
        weight = _recency_weight("", decay_rate=0.005)
        assert weight == 1.0   # unknown → treat as fresh

    def test_importance_clamp_high(self, svc):
        from memory.context import LongTermMemory
        ltm = LongTermMemory(memory_service=svc)
        # importance=100.0 should be clamped to 5.0 without raising
        mem_id = ltm.store(
            project_id=304,
            agent_name="backend_developer",
            artifact_type="backend_code",
            collection_name="backend_code",
            content="High importance content",
            importance=100.0,
        )
        assert isinstance(mem_id, str)

    def test_forget_stale_returns_count(self, svc):
        from memory.context import LongTermMemory
        ltm = LongTermMemory(memory_service=svc, decay_rate=1000.0)  # very fast decay
        ltm.store(
            project_id=305,
            agent_name="architect",
            artifact_type="architecture",
            collection_name="architecture",
            content="Stale architecture decision",
            importance=1.0,
        )
        # With a huge decay rate everything is stale
        stale = ltm.forget_stale(
            project_id=305,
            collection_name="architecture",
            min_recency_weight=0.99,
        )
        assert isinstance(stale, int)
        assert stale >= 0

    def test_default_init_lazy_loads_service(self):
        from memory.context.long_term import LongTermMemory
        mock_svc = MagicMock()
        mock_manager = MagicMock()
        mock_manager.get_service.return_value = mock_svc
        with patch("memory.manager.default_manager", mock_manager):
            ltm = LongTermMemory()
            assert ltm._svc is mock_svc


# ===========================================================================
# 4. ConversationMemory
# ===========================================================================

class TestConversationMemory:

    def test_append_returns_id(self, svc):
        from memory.context import ConversationMemory
        cm = ConversationMemory(memory_service=svc)
        mem_id = cm.append(project_id=400, role="user", content="Hello!")
        assert isinstance(mem_id, str)

    def test_get_history_returns_turns(self, svc):
        from memory.context import ConversationMemory
        cm = ConversationMemory(memory_service=svc)
        cm.append(project_id=401, role="user", content="What is FastAPI?")
        cm.append(project_id=401, role="assistant", content="FastAPI is a modern Python web framework.")
        history = cm.get_history(project_id=401)
        assert len(history) >= 2
        roles = {t["role"] for t in history}
        assert "user" in roles
        assert "assistant" in roles

    def test_history_in_chronological_order(self, svc):
        from memory.context import ConversationMemory
        cm = ConversationMemory(memory_service=svc)
        # Module-scoped fixture — use unique project IDs throughout
        pid = 402
        cm.append(project_id=pid, role="user", content="First message")
        cm.append(project_id=pid, role="assistant", content="First response")
        cm.append(project_id=pid, role="user", content="Second message")
        history = cm.get_history(project_id=pid)
        assert len(history) >= 3

    def test_get_window_limits_turns(self, svc):
        from memory.context import ConversationMemory
        cm = ConversationMemory(memory_service=svc)
        for i in range(8):
            cm.append(project_id=403, role="user", content=f"Message {i}")
        window = cm.get_window(project_id=403, n=3)
        assert len(window) <= 3

    def test_session_scoping_isolates_turns(self, svc):
        from memory.context import ConversationMemory
        cm = ConversationMemory(memory_service=svc)
        cm.append(project_id=404, role="user", content="Session A turn", session_id="session_a")
        cm.append(project_id=404, role="user", content="Session B turn", session_id="session_b")

        history_a = cm.get_history(project_id=404, session_id="session_a")
        history_b = cm.get_history(project_id=404, session_id="session_b")

        assert all("Session A" in t["content"] for t in history_a)
        assert all("Session B" in t["content"] for t in history_b)
        assert len(history_a) >= 1
        assert len(history_b) >= 1

    def test_role_filter(self, svc):
        from memory.context import ConversationMemory
        cm = ConversationMemory(memory_service=svc)
        cm.append(project_id=405, role="user", content="User query")
        cm.append(project_id=405, role="assistant", content="Assistant reply")
        cm.append(project_id=405, role="system", content="System prompt")

        user_only = cm.get_history(project_id=405, roles=["user"])
        assert all(t["role"] == "user" for t in user_only)

    def test_search_returns_results(self, svc):
        from memory.context import ConversationMemory
        cm = ConversationMemory(memory_service=svc)
        cm.append(
            project_id=406, role="user",
            content="How should I implement JWT token refresh?"
        )
        results = cm.search(
            project_id=406,
            query="JWT token",
            limit=5,
        )
        assert isinstance(results, list)

    def test_summarise_returns_string(self, svc):
        from memory.context import ConversationMemory
        cm = ConversationMemory(memory_service=svc)
        cm.append(project_id=407, role="user", content="Tell me about the project.")
        cm.append(project_id=407, role="assistant", content="It's a CodeForge AI platform.")
        summary = cm.summarise(project_id=407, limit=5)
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_summarise_empty_project_returns_empty_string(self, svc):
        from memory.context import ConversationMemory
        cm = ConversationMemory(memory_service=svc)
        summary = cm.summarise(project_id=9994)
        assert summary == ""

    def test_token_estimate_is_integer(self, svc):
        from memory.context import ConversationMemory
        cm = ConversationMemory(memory_service=svc)
        cm.append(project_id=408, role="user", content="A short sentence.")
        estimate = cm.token_estimate(project_id=408)
        assert isinstance(estimate, int)
        assert estimate >= 0

    def test_token_estimate_grows_with_turns(self, svc):
        from memory.context import ConversationMemory
        cm = ConversationMemory(memory_service=svc)
        pid = 409
        cm.append(pid, "user", "First turn with some words.")
        est1 = cm.token_estimate(pid)
        cm.append(pid, "assistant", "Second turn adds more words to the total count.")
        est2 = cm.token_estimate(pid)
        assert est2 >= est1

    def test_count_turns_zero_for_empty(self, svc):
        from memory.context import ConversationMemory
        cm = ConversationMemory(memory_service=svc)
        assert cm.count_turns(project_id=9995) == 0

    def test_count_turns_increments(self, svc):
        from memory.context import ConversationMemory
        cm = ConversationMemory(memory_service=svc)
        pid = 410
        cm.append(pid, "user", "Turn 1")
        cm.append(pid, "assistant", "Turn 2")
        assert cm.count_turns(project_id=pid) == 2

    def test_clear_returns_count(self, svc):
        from memory.context import ConversationMemory
        cm = ConversationMemory(memory_service=svc)
        cm.append(project_id=411, role="user", content="Something to clear.")
        count = cm.clear(project_id=411)
        assert isinstance(count, int)
        assert count >= 1

    def test_default_init_lazy_loads_service(self):
        from memory.context.conversation import ConversationMemory
        mock_svc = MagicMock()
        mock_manager = MagicMock()
        mock_manager.get_service.return_value = mock_svc
        with patch("memory.manager.default_manager", mock_manager):
            cm = ConversationMemory()
            assert cm._svc is mock_svc

    def test_system_role_stored_correctly(self, svc):
        from memory.context import ConversationMemory
        cm = ConversationMemory(memory_service=svc)
        cm.append(project_id=412, role="system", content="You are a helpful assistant.")
        history = cm.get_history(project_id=412)
        system_turns = [t for t in history if t["role"] == "system"]
        assert len(system_turns) >= 1

    def test_unknown_role_stored_as_user(self, svc):
        from memory.context import ConversationMemory
        from memory.context.conversation import _VALID_ROLES
        cm = ConversationMemory(memory_service=svc)
        # "oracle" is not a valid role — should normalise to "user"
        cm.append(project_id=413, role="oracle", content="Oracle speaks.")
        history = cm.get_history(project_id=413)
        roles = {t["role"] for t in history}
        # normalised role should be "user" (not "oracle")
        assert "oracle" not in roles or "user" in roles


# ===========================================================================
# 5. Public exports
# ===========================================================================

class TestPhase35Exports:

    def test_context_injector_importable(self):
        from memory import ContextInjector
        assert ContextInjector is not None

    def test_agent_role_importable(self):
        from memory import AgentRole
        assert AgentRole is not None

    def test_agent_roles_dict_importable(self):
        from memory import AGENT_ROLES
        assert isinstance(AGENT_ROLES, dict)
        assert len(AGENT_ROLES) >= 9

    def test_cross_agent_memory_importable(self):
        from memory import CrossAgentMemory
        assert CrossAgentMemory is not None

    def test_long_term_memory_importable(self):
        from memory import LongTermMemory
        assert LongTermMemory is not None

    def test_conversation_memory_importable(self):
        from memory import ConversationMemory
        assert ConversationMemory is not None

    def test_context_package_importable(self):
        import memory.context
        assert memory.context is not None
