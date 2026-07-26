"""
test_production_hardening.py — Phase 3.6 test suite.

Test categories
---------------
1. MemoryCache            — TTL/LRU correctness, stats, invalidation
2. PerformanceMonitor     — timing, slow queries, throughput, summary
3. Integration tests      — Phases 3.1–3.5 pipeline working end-to-end
4. Regression tests       — Public API backward-compat surface checks
5. Deployment tests       — Config validation, provider boot, degradation

Windows-safe ChromaDB fixture: tempfile.mkdtemp() + shutil.rmtree()
"""
from __future__ import annotations

import shutil
import tempfile
import time
from datetime import datetime, timezone
from typing import List
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_service(tmp_path: str):
    from memory.embeddings.local import LocalEmbeddings
    from memory.service import MemoryService
    from memory.vectorstores.chroma import ChromaVectorStore
    store = ChromaVectorStore(persist_path=tmp_path)
    embed = LocalEmbeddings()
    svc = MemoryService(embedding_provider=embed, vector_store=store)
    return svc, store


@pytest.fixture(scope="module")
def tmp_dir():
    d = tempfile.mkdtemp(prefix="cf_test_prod_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture(scope="module")
def svc(tmp_dir):
    svc, _ = _make_service(tmp_dir)
    return svc


# ===========================================================================
# 1. MemoryCache
# ===========================================================================

class TestMemoryCache:

    def test_get_miss_returns_none(self):
        from memory import MemoryCache
        cache = MemoryCache()
        result = cache.get(project_id=1, collection_name="requirements", query="auth")
        assert result is None

    def test_set_and_get_hit(self):
        from memory import MemoryCache
        cache = MemoryCache()
        results = [{"id": "1", "document": "JWT auth", "similarity_score": 0.9}]
        cache.set(project_id=1, collection_name="requirements", query="auth", results=results)
        cached = cache.get(project_id=1, collection_name="requirements", query="auth")
        assert cached == results

    def test_different_queries_different_keys(self):
        from memory import MemoryCache
        cache = MemoryCache()
        cache.set(project_id=1, collection_name="req", query="auth",
                  results=[{"id": "a"}])
        cache.set(project_id=1, collection_name="req", query="database",
                  results=[{"id": "b"}])
        assert cache.get(1, "req", "auth") != cache.get(1, "req", "database")

    def test_different_projects_different_keys(self):
        from memory import MemoryCache
        cache = MemoryCache()
        cache.set(project_id=1, collection_name="req", query="auth",
                  results=[{"id": "p1"}])
        cache.set(project_id=2, collection_name="req", query="auth",
                  results=[{"id": "p2"}])
        r1 = cache.get(1, "req", "auth")
        r2 = cache.get(2, "req", "auth")
        assert r1 != r2

    def test_ttl_expiry(self):
        from memory import MemoryCache
        cache = MemoryCache(ttl_seconds=0.01)  # 10ms TTL
        cache.set(project_id=1, collection_name="req", query="fast",
                  results=[{"id": "x"}])
        time.sleep(0.05)
        assert cache.get(1, "req", "fast") is None

    def test_lru_eviction(self):
        from memory import MemoryCache
        cache = MemoryCache(max_size=3)
        for i in range(4):
            cache.set(i, "col", f"query{i}", [{"id": str(i)}])
        # The oldest entry (i=0) should have been evicted
        assert cache.size <= 3

    def test_invalidate_specific_entry(self):
        from memory import MemoryCache
        cache = MemoryCache()
        cache.set(1, "req", "auth", [{"id": "a"}])
        removed = cache.invalidate(1, "req", "auth")
        assert removed is True
        assert cache.get(1, "req", "auth") is None

    def test_invalidate_nonexistent_returns_false(self):
        from memory import MemoryCache
        cache = MemoryCache()
        removed = cache.invalidate(9999, "col", "nonexistent")
        assert removed is False

    def test_invalidate_project_removes_all_entries(self):
        from memory import MemoryCache
        cache = MemoryCache()
        cache.set(10, "req", "q1", [{"id": "1"}])
        cache.set(10, "arch", "q2", [{"id": "2"}])
        cache.set(20, "req", "q1", [{"id": "3"}])
        removed = cache.invalidate_project(project_id=10)
        assert removed == 2
        assert cache.get(20, "req", "q1") is not None  # other project unaffected

    def test_clear_wipes_all(self):
        from memory import MemoryCache
        cache = MemoryCache()
        cache.set(1, "col", "q", [{"id": "x"}])
        cache.clear()
        assert cache.size == 0

    def test_hit_rate_calculation(self):
        from memory import MemoryCache
        cache = MemoryCache()
        cache.set(1, "col", "q", [{"id": "x"}])
        cache.get(1, "col", "q")   # hit
        cache.get(1, "col", "miss")  # miss
        assert cache.hits == 1
        assert cache.misses >= 1
        assert 0.0 <= cache.hit_rate <= 1.0

    def test_stats_dict_structure(self):
        from memory import MemoryCache
        cache = MemoryCache(ttl_seconds=60, max_size=100)
        stats = cache.stats()
        assert "size" in stats
        assert "max_size" in stats
        assert "hit_rate" in stats
        assert stats["max_size"] == 100

    def test_evict_expired_removes_stale(self):
        from memory import MemoryCache
        cache = MemoryCache(ttl_seconds=0.01)
        cache.set(1, "col", "q", [{"id": "x"}])
        time.sleep(0.05)
        evicted = cache.evict_expired()
        assert evicted >= 1
        assert cache.size == 0

    def test_cache_key_different_limits(self):
        from memory import MemoryCache
        cache = MemoryCache()
        cache.set(1, "col", "query", [{"id": "a"}], limit=5)
        cache.set(1, "col", "query", [{"id": "b"}], limit=10)
        r5 = cache.get(1, "col", "query", limit=5)
        r10 = cache.get(1, "col", "query", limit=10)
        assert r5 != r10

    def test_importable_from_memory(self):
        from memory import MemoryCache
        assert MemoryCache is not None


# ===========================================================================
# 2. PerformanceMonitor
# ===========================================================================

class TestPerformanceMonitor:

    def test_record_single_sample(self):
        from memory import PerformanceMonitor
        m = PerformanceMonitor()
        m.record("embed_query", 50.0)
        stats = m.summary("embed_query")
        assert stats["count"] == 1
        assert stats["mean_ms"] == 50.0

    def test_record_multiple_samples(self):
        from memory import PerformanceMonitor
        m = PerformanceMonitor()
        for v in [10.0, 20.0, 30.0]:
            m.record("retrieve", v)
        stats = m.summary("retrieve")
        assert stats["count"] == 3
        assert stats["min_ms"] == 10.0
        assert stats["max_ms"] == 30.0
        assert stats["mean_ms"] == 20.0

    def test_p95_computed(self):
        from memory import PerformanceMonitor
        m = PerformanceMonitor()
        for i in range(100):
            m.record("op", float(i + 1))
        stats = m.summary("op")
        assert stats["p95_ms"] is not None
        assert stats["p95_ms"] <= 100.0

    def test_slow_query_logged(self):
        from memory import PerformanceMonitor
        m = PerformanceMonitor(slow_threshold_ms=100.0)
        m.record("slow_op", 500.0)
        slow = m.slow_queries()
        assert len(slow) >= 1
        assert slow[0]["operation"] == "slow_op"

    def test_fast_query_not_in_slow_log(self):
        from memory import PerformanceMonitor
        m = PerformanceMonitor(slow_threshold_ms=100.0)
        m.record("fast_op", 10.0)
        slow = m.slow_queries()
        assert all(e["operation"] != "fast_op" for e in slow)

    def test_slow_queries_custom_threshold(self):
        from memory import PerformanceMonitor
        m = PerformanceMonitor(slow_threshold_ms=50.0)
        m.record("op_a", 200.0)  # logged
        m.record("op_b", 80.0)   # logged at 50ms threshold
        m.record("op_c", 10.0)   # not slow
        # Filter at 100ms — only op_a should show
        slow_100 = m.slow_queries(threshold_ms=100.0)
        assert all(e["duration_ms"] >= 100.0 for e in slow_100)

    def test_timed_decorator(self):
        from memory import PerformanceMonitor
        m = PerformanceMonitor()

        @m.timed("my_function")
        def func():
            time.sleep(0.001)
            return 42

        result = func()
        assert result == 42
        stats = m.summary("my_function")
        assert stats["count"] == 1
        assert stats["mean_ms"] >= 0.0

    def test_measure_context_manager(self):
        from memory import PerformanceMonitor
        m = PerformanceMonitor()
        with m.measure("ctx_op"):
            time.sleep(0.001)
        stats = m.summary("ctx_op")
        assert stats["count"] == 1

    def test_summary_all_operations(self):
        from memory import PerformanceMonitor
        m = PerformanceMonitor()
        m.record("op_x", 10.0)
        m.record("op_y", 20.0)
        all_stats = m.summary()
        assert isinstance(all_stats, dict)
        assert "op_x" in all_stats
        assert "op_y" in all_stats

    def test_summary_empty_operation(self):
        from memory import PerformanceMonitor
        m = PerformanceMonitor()
        stats = m.summary("nonexistent")
        assert stats["count"] == 0
        assert stats["min_ms"] is None

    def test_throughput_positive(self):
        from memory import PerformanceMonitor
        m = PerformanceMonitor()
        for _ in range(10):
            m.record("embed", 100.0)  # 100ms each → 10 ops/sec
        tp = m.throughput("embed")
        assert tp > 0.0

    def test_throughput_no_samples(self):
        from memory import PerformanceMonitor
        m = PerformanceMonitor()
        assert m.throughput("empty_op") == 0.0

    def test_operation_names(self):
        from memory import PerformanceMonitor
        m = PerformanceMonitor()
        m.record("alpha", 1.0)
        m.record("beta", 2.0)
        names = m.operation_names()
        assert names == sorted(names)
        assert "alpha" in names

    def test_reset_specific_operation(self):
        from memory import PerformanceMonitor
        m = PerformanceMonitor()
        m.record("keep", 10.0)
        m.record("drop", 20.0)
        m.reset("drop")
        assert m.summary("drop")["count"] == 0
        assert m.summary("keep")["count"] == 1

    def test_reset_all(self):
        from memory import PerformanceMonitor
        m = PerformanceMonitor()
        m.record("op1", 10.0)
        m.record("op2", 20.0)
        m.reset()
        assert m.summary() == {}

    def test_importable_from_memory(self):
        from memory import PerformanceMonitor
        assert PerformanceMonitor is not None


# ===========================================================================
# 3. Integration — Full pipeline Phases 3.1–3.5
# ===========================================================================

class TestEndToEndIntegration:
    """
    End-to-end test exercising the entire Phase 3 stack in concert.

    Sequence:
      1. Store requirements   (3.4 ProjectMemoryService)
      2. Store architecture   (3.4)
      3. Generate backend file (3.4)
      4. Agent publishes via CrossAgentMemory (3.5)
      5. ContextInjector builds prompt block (3.5)
      6. ConversationMemory records the turn (3.5)
      7. LongTermMemory retrieves with decay  (3.5)
      8. RAGPipeline ingests + retrieves      (3.3)
      9. MemoryCache wraps retrieve call      (3.6)
     10. PerformanceMonitor records timing    (3.6)
    """

    def test_full_pipeline(self, svc):
        from memory.project_memory import ProjectMemoryService
        from memory.context import (
            ContextInjector, CrossAgentMemory, ConversationMemory, LongTermMemory,
        )
        from memory import MemoryCache, PerformanceMonitor
        from memory.rag import RAGPipeline

        pid = 1000
        pms   = ProjectMemoryService(memory_service=svc)
        cam   = CrossAgentMemory(memory_service=svc)
        ci    = ContextInjector(memory_service=svc)
        cm    = ConversationMemory(memory_service=svc)
        ltm   = LongTermMemory(memory_service=svc)
        cache = MemoryCache(ttl_seconds=60)
        monitor = PerformanceMonitor(slow_threshold_ms=500)

        # 1. Store requirements
        with monitor.measure("store_requirement"):
            req_id = pms.store_requirement(
                project_id=pid,
                content="Users shall authenticate with JWT tokens.",
                version=1,
            )
        assert isinstance(req_id, str)

        # 2. Store architecture
        arch_id = pms.store_architecture(
            project_id=pid,
            content="Microservices: FastAPI backend, React frontend.",
        )
        assert isinstance(arch_id, str)

        # 3. Store generated file
        file_id = pms.store_generated_file(
            project_id=pid,
            file_path="backend/auth.py",
            content="from jose import jwt\ndef create_token(sub): ...",
            language="python",
        )
        assert isinstance(file_id, str)

        # 4. Cross-agent publish
        broadcast = cam.broadcast(
            project_id=pid,
            agent_name="security_engineer",
            artifact_type="security_report",
            content="No vulnerabilities found in JWT implementation.",
            version=1,
        )
        assert "mem_id" in broadcast

        # 5. Context injection
        block = ci.build_context_block(
            project_id=pid,
            agent_name="backend_developer",
            user_query="JWT authentication",
        )
        assert isinstance(block, str)

        # 6. Conversation memory
        cm.append(project_id=pid, role="user",
                  content="How should I handle token refresh?")
        cm.append(project_id=pid, role="assistant",
                  content="Use refresh token rotation with short access token TTL.")
        history = cm.get_history(project_id=pid)
        assert len(history) >= 2

        # 7. LongTerm retrieval
        results = ltm.retrieve(
            project_id=pid,
            query="JWT authentication",
            collections=["requirements"],
        )
        assert isinstance(results, list)

        # 8. RAG pipeline
        rag = RAGPipeline.from_service(svc)
        ingest = rag.ingest(
            text="def authenticate_user(token: str) -> User:\n    payload = jwt.decode(token, SECRET)\n    return get_user(payload['sub'])",
            project_id=pid,
            agent_name="backend_developer",
            artifact_type="backend_code",
            collection_name="backend_code",
        )
        assert ingest.stored_chunks >= 1
        retrieved = rag.retrieve(
            query="decode JWT token",
            project_id=pid,
            collection_name="backend_code",
        )
        assert isinstance(retrieved, list)

        # 9. Cache wrapping
        cache_key_args = dict(
            project_id=pid, collection_name="requirements", query="JWT"
        )
        cached = cache.get(**cache_key_args)
        if cached is None:
            fresh = svc.retrieve_memory(pid, "requirements", "JWT")
            cache.set(**cache_key_args, results=fresh)
        second = cache.get(**cache_key_args)
        assert second is not None   # now cached
        assert cache.hits >= 1

        # 10. Performance stats
        stats = monitor.summary("store_requirement")
        assert stats["count"] >= 1

        # Snapshot — final sanity check
        snapshot = pms.get_project_snapshot(project_id=pid)
        assert snapshot.total_artifacts >= 2

    def test_cross_agent_publish_visible_to_other_agents(self, svc):
        from memory.context import CrossAgentMemory
        cam = CrossAgentMemory(memory_service=svc)

        cam.publish(project_id=1001, agent_name="qa_engineer",
                    artifact_type="qa_report", content="All 42 tests pass.", version=1)

        records = cam.read(project_id=1001, source_agent="qa_engineer")
        assert len(records) >= 1

        latest = cam.read_latest(project_id=1001, source_agent="qa_engineer",
                                 artifact_type="qa_report")
        assert latest is not None
        assert "All 42 tests pass." in latest["document"]

    def test_conversation_memory_session_isolation(self, svc):
        from memory.context import ConversationMemory
        cm = ConversationMemory(memory_service=svc)
        pid = 1002
        cm.append(pid, "user", "Session X message", session_id="x")
        cm.append(pid, "user", "Session Y message", session_id="y")
        hx = cm.get_history(pid, session_id="x")
        hy = cm.get_history(pid, session_id="y")
        assert all("Session X" in t["content"] for t in hx)
        assert all("Session Y" in t["content"] for t in hy)


# ===========================================================================
# 4. Regression tests — backward-compat public API surface
# ===========================================================================

class TestRegressionPublicAPI:

    def test_memory_service_store_memory_signature(self, svc):
        """store_memory must accept all Phase 3.1 kwargs."""
        mem_id = svc.store_memory(
            project_id=2000,
            agent_name="architect",
            artifact_type="architecture",
            collection_name="architecture",
            content="Regression test content",
            version=1,
        )
        assert isinstance(mem_id, str)

    def test_memory_service_retrieve_memory_signature(self, svc):
        svc.store_memory(2001, "architect", "architecture", "architecture",
                         "Regression retrieve test", 1)
        results = svc.retrieve_memory(
            project_id=2001,
            collection_name="architecture",
            query="Regression",
        )
        assert isinstance(results, list)

    def test_memory_service_build_agent_context_signature(self, svc):
        from memory.schemas import AgentContext
        ctx = svc.build_agent_context(
            project_id=2002,
            agent_name="backend_developer",
            query="regression test",
        )
        assert isinstance(ctx, AgentContext)

    def test_memory_service_store_conversation_turn(self, svc):
        mem_id = svc.store_conversation_turn(
            project_id=2003, role="user", content="regression"
        )
        assert isinstance(mem_id, str)

    def test_memory_service_get_conversation_history(self, svc):
        svc.store_conversation_turn(2004, "user", "hello")
        history = svc.get_conversation_history(project_id=2004, limit=5)
        assert isinstance(history, list)

    def test_memory_service_record_version(self, svc):
        mem_id = svc.record_version(
            project_id=2005,
            agent_name="architect",
            artifact_type="architecture",
            content="v1 architecture",
            version=1,
        )
        assert isinstance(mem_id, str)

    def test_memory_service_get_version_history(self, svc):
        from memory.schemas import ProjectHistoryEntry
        svc.record_version(2006, "architect", "architecture", "v1", 1)
        history = svc.get_version_history(project_id=2006)
        assert isinstance(history, list)
        assert all(isinstance(e, ProjectHistoryEntry) for e in history)

    def test_memory_service_delete_project_memory(self, svc):
        svc.store_memory(2007, "architect", "architecture", "architecture", "to delete", 1)
        svc.delete_project_memory(project_id=2007)
        remaining = svc.get_project_memory(2007, "architecture")
        assert remaining == []

    def test_chroma_vector_store_collection_types(self):
        from memory.vectorstores.chroma import ChromaVectorStore
        assert isinstance(ChromaVectorStore.COLLECTION_TYPES, list)
        assert len(ChromaVectorStore.COLLECTION_TYPES) == 12

    def test_local_embeddings_backward_compat(self):
        from memory.embeddings.local import LocalEmbeddings
        embed = LocalEmbeddings()
        vec = embed.embed_query("test")
        assert len(vec) > 0         # dimension is configurable (default 1536)
        assert isinstance(vec[0], float)
        docs = embed.embed_documents(["a", "b"])
        assert len(docs) == 2

    def test_schemas_importable_from_old_path(self):
        from memory.schemas import (
            MemoryQuery, MemoryQueryResult, MemoryStoreRequest,
            AgentContext, CollectionName, MemoryMetadata,
            TextChunk, ProviderHealth, ProjectHistoryEntry,
        )
        assert MemoryQuery is not None

    def test_phase34_schemas_importable(self):
        from memory.schemas import (
            ArtifactType, AgentMemoryRecord, GeneratedFileRecord,
            RevisionEntry, ProjectSnapshot, StoreArtifactRequest,
            StoreRevisionRequest, VersionHistoryQuery, MemorySearchRequest,
        )
        assert ArtifactType is not None

    def test_phase35_imports(self):
        from memory import (
            ContextInjector, AgentRole, AGENT_ROLES,
            CrossAgentMemory, LongTermMemory, ConversationMemory,
        )
        assert len(AGENT_ROLES) >= 9

    def test_phase36_imports(self):
        from memory import MemoryCache, PerformanceMonitor
        assert MemoryCache is not None
        assert PerformanceMonitor is not None

    def test_rag_pipeline_from_service(self, svc):
        from memory.rag import RAGPipeline
        pipeline = RAGPipeline.from_service(svc)
        assert pipeline is not None


# ===========================================================================
# 5. Deployment tests
# ===========================================================================

class TestDeploymentConfig:

    def test_memory_settings_loads_defaults(self):
        from memory.config import MemorySettings
        settings = MemorySettings()
        # Field names use the env-var caps convention
        assert settings.EMBEDDING_PROVIDER in ("local", "ollama", "huggingface")
        assert settings.RAG_CHUNK_SIZE > 0
        assert settings.RAG_CHUNK_OVERLAP >= 0

    def test_chroma_path_set(self):
        from memory.config import MemorySettings
        settings = MemorySettings()
        assert settings.CHROMA_PERSIST_PATH is not None
        assert len(str(settings.CHROMA_PERSIST_PATH)) > 0

    def test_local_provider_boots_without_env_vars(self):
        """LocalEmbeddings must work with zero configuration."""
        from memory.embeddings.local import LocalEmbeddings
        embed = LocalEmbeddings()
        # health_check is a method
        assert embed.health_check() is True
        vec = embed.embed_query("boot test")
        assert len(vec) > 0

    def test_default_manager_get_service_returns_service(self):
        from memory.manager import default_manager
        from memory.service import MemoryService
        svc = default_manager.get_service()
        assert isinstance(svc, MemoryService)

    def test_memory_service_no_args_constructor(self):
        """MemoryService() with no args must not raise (uses LocalEmbeddings)."""
        from memory.service import MemoryService
        svc = MemoryService()
        assert svc is not None

    def test_graceful_degradation_ollama_unavailable(self):
        """Resolver must fall back to local if Ollama is unreachable."""
        from memory.embeddings.resolver import resolve_provider
        # Force Ollama as preferred, but it's not running
        provider = resolve_provider(
            preferred="ollama",
            fallback_chain=["ollama", "local"],
        )
        # Must return something functional
        vec = provider.embed_query("graceful degradation test")
        assert len(vec) > 0

    def test_chroma_store_creates_all_collections(self):
        tmp = tempfile.mkdtemp(prefix="cf_test_deploy_")
        try:
            from memory.vectorstores.chroma import ChromaVectorStore
            store = ChromaVectorStore(persist_path=tmp)
            # Access a couple of collections to ensure they are created
            for col in ["requirements", "backend_code", "project_history"]:
                store.get_all(project_id=1, collection_name=col)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_env_var_provider_selection(self):
        """EMBEDDING_PROVIDER env-var drives resolver selection."""
        import os
        from memory.embeddings.resolver import resolve_provider
        original = os.environ.get("EMBEDDING_PROVIDER")
        try:
            os.environ["EMBEDDING_PROVIDER"] = "local"
            provider = resolve_provider(preferred="local", fallback_chain=["local"])
            assert provider.provider_name == "local"
        finally:
            if original is None:
                os.environ.pop("EMBEDDING_PROVIDER", None)
            else:
                os.environ["EMBEDDING_PROVIDER"] = original

    def test_cached_embedding_provider_wraps_local(self):
        from memory.embeddings.local import LocalEmbeddings
        from memory.utils.cache import CachedEmbeddingProvider
        embed = LocalEmbeddings()
        cached = CachedEmbeddingProvider(embed, max_size=64)
        v1 = cached.embed_query("hello")
        v2 = cached.embed_query("hello")   # should hit cache
        assert v1 == v2
        # _hits is the private counter; check via stats
        assert cached._hits >= 1

    def test_memory_manager_health_check(self):
        from memory.manager import MemoryManager
        from memory.schemas import ProviderHealth
        manager = MemoryManager()
        health = manager.health_check()
        # Returns a ProviderHealth schema object
        assert isinstance(health, ProviderHealth)
        assert hasattr(health, "healthy")
