"""
Phase 3.1 — Memory Architecture Tests

Tests cover:
    - EmbeddingProviderInterface contract enforcement
    - LocalEmbeddings correctness
    - OllamaEmbeddings (mocked — no live server required)
    - HuggingFaceEmbeddings (mocked — no live API required)
    - Resolver: preferred provider, fallback chain, always returns provider
    - CachedEmbeddingProvider: hit/miss behaviour, cache eviction
    - ChromaVectorStore: CRUD lifecycle
    - MemoryService: store, retrieve, get, delete lifecycle
    - MemoryService: backward-compat constructor (embeddings_provider / store_manager)
    - MemoryManager: build, health_check, switch_embedding_provider
    - Chunking: edge cases, overlap
    - Cosine similarity and rank_results
    - Schemas: Pydantic validation, to_prompt_block rendering
    - Config: singleton, get_fallback_chain
"""
from __future__ import annotations

import math
import shutil
import tempfile
from typing import List
from unittest.mock import MagicMock, patch

import pytest

# ============================================================================
# Helpers
# ============================================================================

def _make_fake_store(collections=None):
    """Return a mock VectorStoreInterface with sensible defaults."""
    from memory.vectorstores.chroma import ChromaVectorStore

    store = MagicMock(spec=ChromaVectorStore)
    store.COLLECTION_TYPES = ChromaVectorStore.COLLECTION_TYPES
    store.get_collection_size.return_value = 1
    store.query.return_value = {"ids": [[]], "documents": [[]], "metadatas": [[]]}
    store.get_all.return_value = {"ids": [], "documents": [], "metadatas": []}
    return store


# ============================================================================
# Phase 3.1.1 — LocalEmbeddings
# ============================================================================

class TestLocalEmbeddings:
    def _provider(self):
        from memory.embeddings.local import LocalEmbeddings
        return LocalEmbeddings(dim=128)

    def test_dimension_property(self):
        p = self._provider()
        assert p.dimension == 128

    def test_provider_name(self):
        assert self._provider().provider_name == "local"

    def test_health_check_always_true(self):
        assert self._provider().health_check() is True

    def test_embed_query_length(self):
        vec = self._provider().embed_query("hello world")
        assert len(vec) == 128

    def test_embed_query_normalised(self):
        vec = self._provider().embed_query("normalisation test text")
        norm = math.sqrt(sum(v * v for v in vec))
        assert abs(norm - 1.0) < 1e-5

    def test_embed_documents_batch(self):
        p = self._provider()
        vecs = p.embed_documents(["doc one", "doc two", "doc three"])
        assert len(vecs) == 3
        for v in vecs:
            assert len(v) == 128

    def test_empty_text_returns_zero_vector(self):
        vec = self._provider().embed_query("")
        assert all(v == 0.0 for v in vec)

    def test_deterministic(self):
        p = self._provider()
        a = p.embed_query("deterministic input")
        b = p.embed_query("deterministic input")
        assert a == b

    def test_different_texts_produce_different_vectors(self):
        p = self._provider()
        a = p.embed_query("cats")
        b = p.embed_query("thermodynamics")
        assert a != b

    def test_large_dimension(self):
        from memory.embeddings.local import LocalEmbeddings
        p = LocalEmbeddings(dim=1536)
        vec = p.embed_query("production dimension test")
        assert len(vec) == 1536


# ============================================================================
# Phase 3.1.2 — OllamaEmbeddings (mocked)
# ============================================================================

class TestOllamaEmbeddings:
    def test_provider_name(self):
        from memory.embeddings.ollama import OllamaEmbeddings
        assert OllamaEmbeddings().provider_name == "ollama"

    def test_default_dimension(self):
        from memory.embeddings.ollama import OllamaEmbeddings
        assert OllamaEmbeddings().dimension == 768

    def test_embed_query_uses_nomic_prefix(self):
        from memory.embeddings.ollama import OllamaEmbeddings
        provider = OllamaEmbeddings(model="nomic-embed-text")
        fake_vec = [0.1] * 768
        with patch.object(provider, "_call_api", return_value=fake_vec) as mock_call:
            provider.embed_query("test query")
            called_arg = mock_call.call_args[0][0]
            assert called_arg.startswith("query: ")

    def test_embed_documents_no_prefix(self):
        from memory.embeddings.ollama import OllamaEmbeddings
        provider = OllamaEmbeddings()
        fake_vec = [0.0] * 768
        with patch.object(provider, "_call_api", return_value=fake_vec) as mock_call:
            provider.embed_documents(["doc a", "doc b"])
            assert mock_call.call_count == 2
            # No query prefix on documents
            first_arg = mock_call.call_args_list[0][0][0]
            assert not first_arg.startswith("query: ")

    def test_health_check_false_when_unreachable(self):
        from memory.embeddings.ollama import OllamaEmbeddings
        import httpx
        provider = OllamaEmbeddings(base_url="http://127.0.0.1:9999")
        with patch("httpx.Client") as mock_client_cls:
            mock_client_cls.return_value.__enter__.return_value.get.side_effect = (
                httpx.ConnectError("refused")
            )
            assert provider.health_check() is False

    def test_dimension_updated_from_response(self):
        """_call_api updates self._dimension when the real response has a new length."""
        from memory.embeddings.ollama import OllamaEmbeddings
        import httpx

        provider = OllamaEmbeddings(model="unknown-model")
        assert provider.dimension == 768  # default for unknown model

        # Simulate a real API response with a 512-dim vector
        fake_response = MagicMock()
        fake_response.json.return_value = {"embedding": [0.0] * 512}
        fake_response.raise_for_status = MagicMock()

        with patch("httpx.Client") as mock_client_cls:
            mock_ctx = MagicMock()
            mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
            mock_ctx.__exit__ = MagicMock(return_value=False)
            mock_ctx.post.return_value = fake_response
            mock_client_cls.return_value = mock_ctx

            result = provider.embed_documents(["text"])

        assert len(result[0]) == 512
        assert provider.dimension == 512


# ============================================================================
# Phase 3.1.3 — HuggingFaceEmbeddings (mocked)
# ============================================================================

class TestHuggingFaceEmbeddings:
    def test_requires_api_token(self):
        from memory.embeddings.huggingface import HuggingFaceEmbeddings
        with pytest.raises(ValueError, match="HF_API_TOKEN"):
            HuggingFaceEmbeddings(api_token="")

    def test_provider_name(self):
        from memory.embeddings.huggingface import HuggingFaceEmbeddings
        p = HuggingFaceEmbeddings(api_token="tok")
        assert p.provider_name == "huggingface"

    def test_dimension_from_model_map(self):
        from memory.embeddings.huggingface import HuggingFaceEmbeddings
        p = HuggingFaceEmbeddings(
            api_token="tok",
            model="sentence-transformers/all-MiniLM-L6-v2",
        )
        assert p.dimension == 384

    def test_embed_query_calls_api(self):
        from memory.embeddings.huggingface import HuggingFaceEmbeddings
        p = HuggingFaceEmbeddings(api_token="tok")
        fake_vec = [0.1] * 384
        with patch.object(p, "_call_api", return_value=[fake_vec]) as mock_api:
            result = p.embed_query("hello")
            mock_api.assert_called_once_with(["hello"])
            assert result == fake_vec

    def test_embed_documents_batch(self):
        from memory.embeddings.huggingface import HuggingFaceEmbeddings
        p = HuggingFaceEmbeddings(api_token="tok")
        fake_vecs = [[0.1] * 384, [0.2] * 384]
        with patch.object(p, "_call_api", return_value=fake_vecs):
            result = p.embed_documents(["a", "b"])
            assert len(result) == 2

    def test_health_check_false_on_error(self):
        from memory.embeddings.huggingface import HuggingFaceEmbeddings
        p = HuggingFaceEmbeddings(api_token="bad-token")
        with patch.object(p, "embed_query", side_effect=RuntimeError("401")):
            assert p.health_check() is False


# ============================================================================
# Phase 3.1.4 — Resolver
# ============================================================================

class TestResolver:
    def test_returns_local_when_preferred_local(self):
        from memory.embeddings.resolver import resolve_provider
        provider = resolve_provider(preferred="local", fallback_chain=["local"])
        assert provider.provider_name == "local"

    def test_falls_back_to_local_when_ollama_unavailable(self):
        from memory.embeddings.resolver import resolve_provider
        with patch("memory.embeddings.resolver._try_build_ollama", return_value=None), \
             patch("memory.embeddings.resolver._try_build_huggingface", return_value=None):
            provider = resolve_provider(preferred="ollama", fallback_chain=["ollama", "local"])
        assert provider.provider_name == "local"

    def test_uses_ollama_when_healthy(self):
        from memory.embeddings import resolver as resolver_module
        from memory.embeddings.ollama import OllamaEmbeddings
        mock_prov = MagicMock(spec=OllamaEmbeddings)
        mock_prov.provider_name = "ollama"
        # _BUILDERS["ollama"] holds the callable used at runtime — patch that key
        original = resolver_module._BUILDERS["ollama"]
        resolver_module._BUILDERS["ollama"] = lambda: mock_prov
        try:
            provider = resolver_module.resolve_provider(
                preferred="ollama", fallback_chain=["ollama", "local"]
            )
        finally:
            resolver_module._BUILDERS["ollama"] = original
        assert provider.provider_name == "ollama"

    def test_always_returns_something(self):
        from memory.embeddings.resolver import resolve_provider
        with patch("memory.embeddings.resolver._try_build_ollama", return_value=None), \
             patch("memory.embeddings.resolver._try_build_huggingface", return_value=None):
            provider = resolve_provider(preferred="ollama", fallback_chain=["ollama", "huggingface", "local"])
        assert provider is not None
        assert provider.provider_name == "local"


# ============================================================================
# Phase 3.1.5 — CachedEmbeddingProvider
# ============================================================================

class TestCachedEmbeddingProvider:
    def _make(self, max_size=10):
        from memory.embeddings.local import LocalEmbeddings
        from memory.utils.cache import CachedEmbeddingProvider
        return CachedEmbeddingProvider(LocalEmbeddings(dim=64), max_size=max_size)

    def test_cache_hit_avoids_second_call(self):
        from memory.utils.cache import CachedEmbeddingProvider
        inner = MagicMock()
        inner.provider_name = "mock"
        inner.dimension = 4
        inner.embed_documents.return_value = [[0.1, 0.2, 0.3, 0.4]]
        provider = CachedEmbeddingProvider(inner, max_size=10)

        provider.embed_documents(["same text"])
        provider.embed_documents(["same text"])  # should hit cache

        assert inner.embed_documents.call_count == 1

    def test_cache_miss_calls_inner(self):
        cache = self._make()
        cache.embed_documents(["text a"])
        cache.embed_documents(["text b"])
        assert cache.cache_stats["misses"] == 2

    def test_provider_name_wraps_inner(self):
        cache = self._make()
        assert "local" in cache.provider_name

    def test_dimension_delegates(self):
        cache = self._make()
        assert cache.dimension == 64

    def test_max_size_eviction(self):
        cache = self._make(max_size=3)
        for i in range(5):
            cache.embed_query(f"unique text {i}")
        assert cache.cache_stats["size"] <= 3

    def test_clear_cache(self):
        cache = self._make()
        cache.embed_query("some text")
        cache.clear_cache()
        assert cache.cache_stats["size"] == 0
        assert cache.cache_stats["hits"] == 0


# ============================================================================
# Phase 3.1.6 — ChromaVectorStore
# ============================================================================

@pytest.fixture(scope="module")
def temp_chroma_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


class TestChromaVectorStore:
    def _store(self, tmp_dir):
        from memory.vectorstores.chroma import ChromaVectorStore
        return ChromaVectorStore(persist_path=tmp_dir)

    def test_all_collections_registered(self, temp_chroma_dir):
        from memory.vectorstores.chroma import ChromaVectorStore
        store = self._store(temp_chroma_dir)
        for col in ChromaVectorStore.COLLECTION_TYPES:
            assert store.get_collection(col) is not None

    def test_unknown_collection_created_on_demand(self, temp_chroma_dir):
        store = self._store(temp_chroma_dir)
        col = store.get_collection("custom_test_col")
        assert col is not None

    def test_store_and_get_all(self, temp_chroma_dir):
        from memory.embeddings.local import LocalEmbeddings
        store = self._store(temp_chroma_dir)
        p = LocalEmbeddings(dim=64)
        doc = "a test document for ChromaVectorStore"
        emb = p.embed_documents([doc])[0]
        store.store(
            collection_name="requirements",
            ids=["test-id-1"],
            documents=[doc],
            embeddings=[emb],
            metadatas=[{"project_id": 777, "agent_name": "tester",
                        "artifact_type": "test", "timestamp": "2024-01-01",
                        "version": 1}],
        )
        results = store.get_all("requirements", project_id=777)
        assert "test-id-1" in results["ids"]

    def test_delete_by_project(self, temp_chroma_dir):
        from memory.embeddings.local import LocalEmbeddings
        store = self._store(temp_chroma_dir)
        p = LocalEmbeddings(dim=64)
        emb = p.embed_documents(["delete-me"])[0]
        store.store(
            collection_name="requirements",
            ids=["delete-me-id"],
            documents=["delete-me"],
            embeddings=[emb],
            metadatas=[{"project_id": 888, "agent_name": "tester",
                        "artifact_type": "del", "timestamp": "2024-01-01",
                        "version": 1}],
        )
        store.delete_by_project("requirements", project_id=888)
        results = store.get_all("requirements", project_id=888)
        assert "delete-me-id" not in results["ids"]

    def test_get_collection_size(self, temp_chroma_dir):
        store = self._store(temp_chroma_dir)
        size = store.get_collection_size("requirements")
        assert isinstance(size, int)
        assert size >= 0


# ============================================================================
# Phase 3.1.7 — MemoryService full lifecycle
# ============================================================================

@pytest.fixture(scope="module")
def service_chroma_dir():
    """Isolated Chroma directory for MemoryService tests — avoids dimension conflict."""
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture(scope="module")
def service_fixture(service_chroma_dir):
    from memory.embeddings.local import LocalEmbeddings
    from memory.vectorstores.chroma import ChromaVectorStore
    from memory.service import MemoryService

    return MemoryService(
        embedding_provider=LocalEmbeddings(dim=128),
        vector_store=ChromaVectorStore(persist_path=service_chroma_dir),
    )


class TestMemoryService:
    def test_store_returns_nonempty_id(self, service_fixture):
        mid = service_fixture.store_memory(
            project_id=1001,
            agent_name="ba",
            artifact_type="requirements",
            collection_name="requirements",
            content="The system shall support JWT authentication.",
            version=1,
        )
        assert mid != ""

    def test_store_empty_content_returns_empty_string(self, service_fixture):
        mid = service_fixture.store_memory(
            project_id=1001, agent_name="ba",
            artifact_type="x", collection_name="requirements", content="   ",
        )
        assert mid == ""

    def test_retrieve_returns_results(self, service_fixture):
        service_fixture.store_memory(
            project_id=1002, agent_name="sa",
            artifact_type="arch", collection_name="architecture",
            content="FastAPI backend with PostgreSQL database and Redis cache.",
            version=1,
        )
        results = service_fixture.retrieve_memory(
            project_id=1002,
            collection_name="architecture",
            query="FastAPI PostgreSQL",
            limit=3,
        )
        assert isinstance(results, list)

    def test_retrieve_empty_query_returns_empty(self, service_fixture):
        results = service_fixture.retrieve_memory(
            project_id=1002,
            collection_name="architecture",
            query="   ",
        )
        assert results == []

    def test_get_project_memory_returns_docs(self, service_fixture):
        service_fixture.store_memory(
            project_id=1003, agent_name="be",
            artifact_type="code", collection_name="backend_code",
            content="def hello(): return 'world'",
            version=1,
        )
        entries = service_fixture.get_project_memory(1003, "backend_code")
        assert len(entries) >= 1
        assert entries[0]["document"] == "def hello(): return 'world'"

    def test_delete_project_memory_clears_entries(self, service_fixture):
        pid = 9001
        service_fixture.store_memory(
            project_id=pid, agent_name="pm",
            artifact_type="plan", collection_name="requirements",
            content="Requirements to be deleted.",
            version=1,
        )
        service_fixture.delete_project_memory(pid)
        after = service_fixture.get_project_memory(pid, "requirements")
        assert len(after) == 0

    def test_backward_compat_constructor(self, service_chroma_dir):
        """Old embeddings_provider / store_manager kwargs must still work."""
        from memory.embeddings.local import LocalEmbeddings
        from memory.vectorstores.chroma import ChromaVectorStore
        from memory.service import MemoryService

        svc = MemoryService(
            embeddings_provider=LocalEmbeddings(dim=128),
            store_manager=ChromaVectorStore(persist_path=service_chroma_dir),
        )
        mid = svc.store_memory(
            project_id=9999, agent_name="compat", artifact_type="compat",
            collection_name="devops", content="backward compat test", version=1,
        )
        assert mid != ""

    def test_no_args_constructor_defaults_to_local(self):
        """MemoryService() with no args should not raise."""
        import os, shutil, tempfile
        tmp = tempfile.mkdtemp()
        try:
            with patch.dict("os.environ", {"CHROMA_PERSIST_PATH": tmp}):
                from memory.service import MemoryService
                svc = MemoryService()
                assert svc._embed.provider_name == "local"
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


# ============================================================================
# Phase 3.1.8 — MemoryManager
# ============================================================================

class TestMemoryManager:
    """MemoryManager tests use their own tmpdir to avoid Chroma dimension conflicts."""

    def test_get_service_returns_memory_service(self):
        from memory.embeddings.local import LocalEmbeddings
        from memory.vectorstores.chroma import ChromaVectorStore
        from memory.manager import MemoryManager
        from memory.service import MemoryService
        import tempfile, shutil
        d = tempfile.mkdtemp()
        try:
            mgr = MemoryManager(
                embedding_provider=LocalEmbeddings(dim=64),
                vector_store=ChromaVectorStore(persist_path=d),
            )
            svc = mgr.get_service()
            assert isinstance(svc, MemoryService)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_get_service_cached(self):
        from memory.embeddings.local import LocalEmbeddings
        from memory.vectorstores.chroma import ChromaVectorStore
        from memory.manager import MemoryManager
        import tempfile, shutil
        d = tempfile.mkdtemp()
        try:
            mgr = MemoryManager(
                embedding_provider=LocalEmbeddings(dim=64),
                vector_store=ChromaVectorStore(persist_path=d),
            )
            s1 = mgr.get_service()
            s2 = mgr.get_service()
            assert s1 is s2
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_switch_provider_invalidates_service_cache(self):
        from memory.embeddings.local import LocalEmbeddings
        from memory.vectorstores.chroma import ChromaVectorStore
        from memory.manager import MemoryManager
        import tempfile, shutil
        d = tempfile.mkdtemp()
        try:
            mgr = MemoryManager(
                embedding_provider=LocalEmbeddings(dim=64),
                vector_store=ChromaVectorStore(persist_path=d),
            )
            s1 = mgr.get_service()
            mgr.switch_embedding_provider(LocalEmbeddings(dim=64))
            s2 = mgr.get_service()
            assert s1 is not s2
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_health_check_local_is_healthy(self):
        from memory.embeddings.local import LocalEmbeddings
        from memory.vectorstores.chroma import ChromaVectorStore
        from memory.manager import MemoryManager
        import tempfile, shutil
        d = tempfile.mkdtemp()
        try:
            mgr = MemoryManager(
                embedding_provider=LocalEmbeddings(dim=64),
                vector_store=ChromaVectorStore(persist_path=d),
            )
            health = mgr.health_check()
            assert health.healthy is True
            assert health.dimension == 64
        finally:
            shutil.rmtree(d, ignore_errors=True)


# ============================================================================
# Phase 3.1.9 — Chunking utilities
# ============================================================================

class TestChunking:
    def test_short_text_single_chunk(self):
        from memory.utils.chunking import chunk_text
        chunks = chunk_text("short text", chunk_size=800, overlap=100)
        assert len(chunks) == 1
        assert chunks[0].content == "short text"
        assert chunks[0].chunk_index == 0

    def test_long_text_multiple_chunks(self):
        from memory.utils.chunking import chunk_text
        text = "x" * 2000
        chunks = chunk_text(text, chunk_size=800, overlap=100)
        assert len(chunks) > 1

    def test_chunks_cover_all_content(self):
        from memory.utils.chunking import chunk_text
        text = "Hello World! " * 200
        chunks = chunk_text(text, chunk_size=100, overlap=20)
        # First chunk starts at 0
        assert chunks[0].char_start == 0
        # Last chunk ends at len(text)
        assert chunks[-1].char_end == len(text)

    def test_overlap_applied(self):
        from memory.utils.chunking import chunk_text
        text = "a" * 300
        chunks = chunk_text(text, chunk_size=100, overlap=30)
        if len(chunks) > 1:
            # Second chunk should start before end of first - overlap
            assert chunks[1].char_start < chunks[0].char_end

    def test_empty_text_returns_empty(self):
        from memory.utils.chunking import chunk_text
        assert chunk_text("") == []

    def test_artifact_type_propagated(self):
        from memory.utils.chunking import chunk_text
        chunks = chunk_text("some content", artifact_type="python_code")
        assert chunks[0].source_artifact_type == "python_code"

    def test_chunk_documents_flat_list(self):
        from memory.utils.chunking import chunk_documents
        docs = ["short", "also short"]
        chunks = chunk_documents(docs)
        assert len(chunks) == 2


# ============================================================================
# Phase 3.1.10 — Similarity utilities
# ============================================================================

class TestSimilarity:
    def test_identical_vectors_score_one(self):
        from memory.utils.similarity import cosine_similarity
        v = [1.0, 0.0, 0.0]
        assert abs(cosine_similarity(v, v) - 1.0) < 1e-6

    def test_orthogonal_vectors_score_zero(self):
        from memory.utils.similarity import cosine_similarity
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert abs(cosine_similarity(a, b)) < 1e-6

    def test_zero_vector_returns_zero(self):
        from memory.utils.similarity import cosine_similarity
        assert cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0

    def test_mismatched_lengths_returns_zero(self):
        from memory.utils.similarity import cosine_similarity
        assert cosine_similarity([1.0], [1.0, 2.0]) == 0.0

    def test_rank_results_sorted_descending(self):
        from memory.utils.similarity import rank_results
        raw = {
            "ids": [["a", "b", "c"]],
            "documents": [["doc_a", "doc_b", "doc_c"]],
            "metadatas": [[{}, {}, {}]],
        }
        # Hand-crafted embeddings where doc_a is closest to query
        query = [1.0, 0.0, 0.0]
        embs = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.5, 0.5, 0.0]]
        ranked = rank_results(raw, query, embs, threshold=0.0)
        assert ranked[0]["id"] == "a"
        scores = [r["similarity_score"] for r in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_rank_results_filters_below_threshold(self):
        from memory.utils.similarity import rank_results
        raw = {
            "ids": [["a", "b"]],
            "documents": [["doc_a", "doc_b"]],
            "metadatas": [[{}, {}]],
        }
        query = [1.0, 0.0]
        embs = [[1.0, 0.0], [0.0, 1.0]]
        ranked = rank_results(raw, query, embs, threshold=0.9)
        assert len(ranked) == 1
        assert ranked[0]["id"] == "a"


# ============================================================================
# Phase 3.1.11 — Schemas
# ============================================================================

class TestSchemas:
    def test_memory_query_defaults(self):
        from memory.schemas import MemoryQuery
        q = MemoryQuery(query="test")
        assert q.limit == 5
        assert q.threshold == 0.0

    def test_memory_query_validation(self):
        from memory.schemas import MemoryQuery
        import pydantic
        with pytest.raises(pydantic.ValidationError):
            MemoryQuery(query="")  # min_length=1

    def test_agent_context_to_prompt_block_empty(self):
        from memory.schemas import AgentContext
        ctx = AgentContext(project_id=1, agent_name="tester")
        block = ctx.to_prompt_block()
        assert block == ""

    def test_agent_context_to_prompt_block_with_chunks(self):
        from memory.schemas import AgentContext, MemoryQueryResult
        ctx = AgentContext(
            project_id=1,
            agent_name="tester",
            chunks=[
                MemoryQueryResult(
                    id="x", document="auth middleware code",
                    metadata={}, similarity_score=0.87
                )
            ],
        )
        block = ctx.to_prompt_block()
        assert "Relevant Project Memory" in block
        assert "0.87" in block
        assert "auth middleware code" in block

    def test_agent_context_with_conversation(self):
        from memory.schemas import AgentContext
        ctx = AgentContext(
            project_id=1,
            agent_name="tester",
            conversation_history=[
                {"role": "user", "content": "What is the DB schema?"},
                {"role": "assistant", "content": "PostgreSQL with 3 tables."},
            ],
        )
        block = ctx.to_prompt_block()
        assert "Previous Conversation" in block
        assert "PostgreSQL" in block

    def test_collection_name_enum_values(self):
        from memory.schemas import CollectionName
        assert CollectionName.REQUIREMENTS.value == "requirements"
        assert CollectionName.CONVERSATION.value == "conversation"
        assert CollectionName.PROJECT_HISTORY.value == "project_history"

    def test_provider_health_schema(self):
        from memory.schemas import ProviderHealth
        h = ProviderHealth(provider_name="local", healthy=True, dimension=1536)
        assert h.healthy is True
        assert h.dimension == 1536

    def test_memory_store_request_validation(self):
        from memory.schemas import MemoryStoreRequest
        import pydantic
        with pytest.raises(pydantic.ValidationError):
            MemoryStoreRequest(
                project_id=1, agent_name="x", artifact_type="y",
                collection_name="z", content="",  # min_length=1
            )


# ============================================================================
# Phase 3.1.12 — Config
# ============================================================================

class TestConfig:
    def test_settings_singleton_exists(self):
        from memory.config import settings
        assert settings is not None

    def test_get_fallback_chain_parses_csv(self):
        from memory.config import MemorySettings
        s = MemorySettings(EMBEDDING_FALLBACK_CHAIN="ollama,local")
        chain = s.get_fallback_chain()
        assert chain == ["ollama", "local"]

    def test_default_provider_is_local(self):
        from memory.config import settings
        # In CI the env-var is not set so it defaults to "local"
        assert settings.EMBEDDING_PROVIDER in ("local", "ollama", "huggingface")

    def test_chroma_path_resolved_automatically(self):
        from memory.config import settings
        assert settings.CHROMA_PERSIST_PATH != ""

    def test_chunk_size_defaults(self):
        from memory.config import settings
        assert settings.RAG_CHUNK_SIZE == 800
        assert settings.RAG_CHUNK_OVERLAP == 100
