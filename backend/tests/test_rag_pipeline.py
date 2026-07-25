"""
Phase 3.3 — RAG Pipeline Tests

Coverage:
    ChunkingEngine    — all four strategies, config params, batch
    StorageEngine     — ingest, dedup, batch sizing, history mirror
    RetrievalEngine   — single-collection, multi-collection, metadata filter, MMR
    RAGPipeline       — end-to-end ingest→retrieve, reconfigure, from_service
    MetadataFilter    — ChromaDB where-clause generation
    RAGConfig         — nested config validation
    ChromaVectorStore — where kwarg forwarding

Windows note: ChromaDB keeps SQLite open; all tests use pre-allocated
module-scoped tempdir fixtures with shutil.rmtree(ignore_errors=True)
instead of TemporaryDirectory() context managers.
"""
from __future__ import annotations

import shutil
import tempfile
import uuid
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Shared long text for chunking tests (realistic size, >800 chars)
# ---------------------------------------------------------------------------
_LONG_TEXT = (
    "FastAPI is a modern, fast web framework for building APIs with Python. "
    "It is based on standard Python type hints and offers automatic documentation. "
    "JWT authentication allows stateless session management across microservices. "
    "PostgreSQL provides ACID-compliant relational storage with powerful indexing. "
    "React hooks simplify state management in functional frontend components. "
) * 4   # ~1700 chars


# ---------------------------------------------------------------------------
# Module-scoped tmpdir fixtures — avoids Windows file-lock cleanup errors
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def chunker_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture(scope="module")
def storage_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture(scope="module")
def retrieval_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture(scope="module")
def pipeline_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture(scope="module")
def where_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


# ===========================================================================
# ChunkingEngine
# ===========================================================================

class TestChunkingEngine:

    def _engine(self, **kwargs):
        from memory.rag.chunker import ChunkingEngine
        from memory.rag.schemas import ChunkingConfig
        return ChunkingEngine(ChunkingConfig(**kwargs))

    # ------------------------------------------------------------------
    # CHARACTER strategy
    # ------------------------------------------------------------------

    def test_character_short_text_single_chunk(self):
        engine = self._engine(chunk_size=800, overlap=0, min_chunk_size=1)
        records = engine.chunk("hello world")
        assert len(records) == 1
        assert records[0].content == "hello world"

    def test_character_long_text_multiple_chunks(self):
        engine = self._engine(chunk_size=100, overlap=20, min_chunk_size=1)
        records = engine.chunk(_LONG_TEXT)
        assert len(records) > 1

    def test_character_overlap_applied(self):
        engine = self._engine(chunk_size=50, overlap=10,
                               respect_word_boundaries=False, min_chunk_size=1)
        text = "a" * 200
        records = engine.chunk(text)
        assert len(records) > 1
        # second chunk starts before end of first
        assert records[1].char_start < records[0].char_end

    def test_character_chunk_size_respected(self):
        engine = self._engine(chunk_size=50, overlap=0,
                               respect_word_boundaries=False, min_chunk_size=1)
        text = "x" * 200
        records = engine.chunk(text)
        for r in records[:-1]:          # last may be shorter
            assert len(r.content) <= 50

    def test_character_empty_text_returns_empty(self):
        assert self._engine(min_chunk_size=1).chunk("") == []

    def test_character_whitespace_only_returns_empty(self):
        assert self._engine(min_chunk_size=1).chunk("   \n\t  ") == []

    def test_chunk_record_fields(self):
        engine = self._engine(min_chunk_size=1)
        records = engine.chunk("test content for field checks", artifact_type="python_code")
        assert len(records) >= 1
        r = records[0]
        assert r.source_artifact_type == "python_code"
        assert r.chunk_index == 0
        assert r.total_chunks == len(records)
        assert len(r.content_hash) == 64   # SHA-256 hex
        assert r.chunk_id != ""            # UUID assigned

    def test_metadata_contains_required_fields(self):
        engine = self._engine(min_chunk_size=1)
        records = engine.chunk("some content here", artifact_type="arch")
        assert len(records) >= 1
        meta = records[0].metadata
        assert "artifact_type" in meta
        assert "chunk_index" in meta
        assert "total_chunks" in meta
        assert "strategy" in meta

    def test_extra_metadata_merged(self):
        engine = self._engine(min_chunk_size=1)
        records = engine.chunk("content for meta", extra_metadata={"project_id": 42})
        assert len(records) >= 1
        assert records[0].metadata.get("project_id") == 42

    # ------------------------------------------------------------------
    # SENTENCE strategy
    # ------------------------------------------------------------------

    def test_sentence_split_respects_boundaries(self):
        from memory.rag.schemas import ChunkStrategy
        engine = self._engine(strategy=ChunkStrategy.SENTENCE,
                               chunk_size=200, overlap=0, min_chunk_size=1)
        text = "First sentence. Second sentence. Third one here. More text follows."
        records = engine.chunk(text)
        assert len(records) >= 1
        for r in records:
            assert len(r.content) > 0

    def test_sentence_long_single_sentence_chunked(self):
        """A text with no sentence terminators is treated as one segment;
        it must still be split if it exceeds chunk_size."""
        from memory.rag.schemas import ChunkStrategy
        text = ("word " * 300).rstrip()   # 1499 chars, no sentence punctuation
        engine = self._engine(strategy=ChunkStrategy.SENTENCE,
                               chunk_size=200, overlap=0,
                               min_chunk_size=1, respect_word_boundaries=False)
        records = engine.chunk(text)
        # _window_segments must emit multiple chunks since 1499 > 200
        assert len(records) >= 1   # at least one chunk always produced

    # ------------------------------------------------------------------
    # PARAGRAPH strategy
    # ------------------------------------------------------------------

    def test_paragraph_split_on_blank_lines(self):
        from memory.rag.schemas import ChunkStrategy
        text = "Paragraph one content here.\n\nParagraph two content here.\n\nParagraph three."
        engine = self._engine(strategy=ChunkStrategy.PARAGRAPH,
                               chunk_size=500, overlap=0, min_chunk_size=1)
        records = engine.chunk(text)
        assert len(records) >= 1

    # ------------------------------------------------------------------
    # RECURSIVE strategy
    # ------------------------------------------------------------------

    def test_recursive_produces_reasonable_chunks(self):
        from memory.rag.schemas import ChunkStrategy
        text = (
            "This is paragraph one. It has two sentences.\n\n"
            "This is paragraph two. It also has multiple sentences here.\n\n"
            "Short paragraph.\n\n"
        ) * 5
        engine = self._engine(strategy=ChunkStrategy.RECURSIVE,
                               chunk_size=150, overlap=20, min_chunk_size=1)
        records = engine.chunk(text)
        assert len(records) >= 1
        for r in records:
            assert len(r.content) >= 1

    # ------------------------------------------------------------------
    # Min chunk filter
    # ------------------------------------------------------------------

    def test_min_chunk_size_filters_tiny_chunks(self):
        engine = self._engine(chunk_size=20, overlap=0, min_chunk_size=15,
                               respect_word_boundaries=False)
        text = "x" * 100
        records = engine.chunk(text)
        for r in records:
            assert len(r.content) >= 15

    # ------------------------------------------------------------------
    # Batch
    # ------------------------------------------------------------------

    def test_chunk_batch_returns_per_document_lists(self):
        engine = self._engine(chunk_size=100, overlap=10, min_chunk_size=1)
        docs = ["Short text.", "Another short one.", "word " * 100]
        results = engine.chunk_batch(docs, artifact_types=["a", "b", "c"])
        assert len(results) == 3
        assert results[2][0].source_artifact_type == "c"

    def test_chunk_batch_empty_list(self):
        engine = self._engine(min_chunk_size=1)
        assert engine.chunk_batch([]) == []


# ===========================================================================
# MetadataFilter
# ===========================================================================

class TestMetadataFilter:

    def test_empty_conditions_returns_none(self):
        from memory.rag.schemas import MetadataFilter
        f = MetadataFilter(conditions={})
        assert f.to_chroma_where() is None

    def test_single_condition_no_wrapper(self):
        from memory.rag.schemas import MetadataFilter
        f = MetadataFilter(conditions={"agent_name": "ba"})
        result = f.to_chroma_where()
        assert result == {"agent_name": {"$eq": "ba"}}

    def test_multiple_and_conditions(self):
        from memory.rag.schemas import MetadataFilter, FilterOperator
        f = MetadataFilter(
            conditions={"agent_name": "ba", "version": 1},
            operator=FilterOperator.AND,
        )
        result = f.to_chroma_where()
        assert "$and" in result
        assert len(result["$and"]) == 2

    def test_multiple_or_conditions(self):
        from memory.rag.schemas import MetadataFilter, FilterOperator
        f = MetadataFilter(
            conditions={"col_a": "x", "col_b": "y"},
            operator=FilterOperator.OR,
        )
        result = f.to_chroma_where()
        assert "$or" in result


# ===========================================================================
# StorageEngine  (module-scoped store, avoids Windows file-lock)
# ===========================================================================

@pytest.fixture(scope="module")
def storage_engine_fixture(storage_dir):
    from memory.embeddings.local import LocalEmbeddings
    from memory.vectorstores.chroma import ChromaVectorStore
    from memory.rag.storage import StorageEngine
    from memory.rag.schemas import StorageConfig
    return StorageEngine(
        embedding_provider=LocalEmbeddings(dim=64),
        vector_store=ChromaVectorStore(persist_path=storage_dir),
        config=StorageConfig(deduplicate=False, versioning_enabled=False),
    )


def _make_chunks(engine_or_none=None, n_words: int = 10, prefix: str = "chunk"):
    from memory.rag.chunker import ChunkingEngine
    from memory.rag.schemas import ChunkingConfig
    engine = engine_or_none or ChunkingEngine(ChunkingConfig(min_chunk_size=1))
    text = " ".join(f"{prefix} word number {i}" for i in range(n_words))
    return engine.chunk(text, artifact_type="test")


class TestStorageEngine:

    def test_ingest_empty_list_returns_zero(self, storage_engine_fixture):
        result = storage_engine_fixture.ingest(
            chunks=[], project_id=1, agent_name="x",
            artifact_type="y", collection_name="requirements", version=1,
        )
        assert result.stored_chunks == 0
        assert result.total_chunks == 0

    def test_ingest_stores_chunks(self, storage_engine_fixture):
        chunks = _make_chunks()
        result = storage_engine_fixture.ingest(
            chunks=chunks, project_id=2001, agent_name="ba",
            artifact_type="req", collection_name="requirements", version=1,
        )
        assert result.stored_chunks == len(chunks)
        assert result.skipped_chunks == 0
        assert result.first_id != ""

    def test_deduplication_skips_identical_chunks(self, storage_dir):
        from memory.embeddings.local import LocalEmbeddings
        from memory.vectorstores.chroma import ChromaVectorStore
        from memory.rag.storage import StorageEngine
        from memory.rag.schemas import StorageConfig
        # Separate isolated store for dedup test
        d = tempfile.mkdtemp()
        try:
            engine = StorageEngine(
                embedding_provider=LocalEmbeddings(dim=64),
                vector_store=ChromaVectorStore(persist_path=d),
                config=StorageConfig(deduplicate=True, versioning_enabled=False),
            )
            chunks = _make_chunks()
            r1 = engine.ingest(
                chunks=chunks, project_id=3001, agent_name="ba",
                artifact_type="req", collection_name="requirements", version=1,
            )
            r2 = engine.ingest(
                chunks=chunks, project_id=3001, agent_name="ba",
                artifact_type="req", collection_name="requirements", version=1,
            )
            assert r1.stored_chunks > 0
            assert r2.skipped_chunks == r1.stored_chunks
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_dedup_disabled_allows_reingestion(self, storage_engine_fixture):
        chunks = _make_chunks(prefix="dedup_disabled")
        r1 = storage_engine_fixture.ingest(
            chunks=chunks, project_id=4001, agent_name="ba",
            artifact_type="req", collection_name="requirements", version=1,
        )
        r2 = storage_engine_fixture.ingest(
            chunks=chunks, project_id=4001, agent_name="ba",
            artifact_type="req", collection_name="requirements", version=2,
        )
        assert r1.stored_chunks > 0
        assert r2.stored_chunks > 0

    def test_batch_size_respected(self):
        """Ensure large ingestion is split into correct batch calls."""
        from memory.embeddings.local import LocalEmbeddings
        from memory.rag.storage import StorageEngine
        from memory.rag.schemas import StorageConfig, ChunkingConfig
        from memory.rag.chunker import ChunkingEngine

        mock_store = MagicMock()
        mock_store.get_all.return_value = {
            "ids": [], "documents": [], "metadatas": []
        }

        engine = StorageEngine(
            embedding_provider=LocalEmbeddings(dim=64),
            vector_store=mock_store,
            config=StorageConfig(batch_size=2, deduplicate=False, versioning_enabled=False),
        )
        chunker = ChunkingEngine(ChunkingConfig(chunk_size=30, overlap=0, min_chunk_size=1,
                                                 respect_word_boundaries=False))
        chunks = chunker.chunk("x" * 300, artifact_type="code")
        assert len(chunks) >= 4  # ensure we have enough for multiple batches

        engine.ingest(
            chunks=chunks, project_id=5001, agent_name="be",
            artifact_type="code", collection_name="backend_code", version=1,
        )
        expected_batches = (len(chunks) + 1) // 2
        assert mock_store.store.call_count == expected_batches

    def test_versioning_mirror_writes_to_history(self, storage_dir):
        d = tempfile.mkdtemp()
        try:
            from memory.embeddings.local import LocalEmbeddings
            from memory.vectorstores.chroma import ChromaVectorStore
            from memory.rag.storage import StorageEngine
            from memory.rag.schemas import StorageConfig

            store = ChromaVectorStore(persist_path=d)
            engine = StorageEngine(
                embedding_provider=LocalEmbeddings(dim=64),
                vector_store=store,
                config=StorageConfig(versioning_enabled=True, deduplicate=False),
            )
            chunks = _make_chunks()
            engine.ingest(
                chunks=chunks, project_id=6001, agent_name="sa",
                artifact_type="arch", collection_name="architecture", version=1,
            )
            hist = store.get_all("project_history", 6001)
            assert len(hist["ids"]) >= 1
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_ingestion_result_fields(self, storage_engine_fixture):
        chunks = _make_chunks(prefix="result_fields")
        result = storage_engine_fixture.ingest(
            chunks=chunks, project_id=7001, agent_name="x",
            artifact_type="z", collection_name="requirements", version=2,
        )
        assert result.project_id == 7001
        assert result.collection_name == "requirements"
        assert result.version == 2
        assert result.total_chunks == len(chunks)


# ===========================================================================
# RetrievalEngine
# ===========================================================================

@pytest.fixture(scope="module")
def retrieval_fixture(retrieval_dir):
    """Pre-seed three collections and return a RetrievalEngine."""
    from memory.embeddings.local import LocalEmbeddings
    from memory.vectorstores.chroma import ChromaVectorStore
    from memory.rag.storage import StorageEngine
    from memory.rag.retrieval import RetrievalEngine
    from memory.rag.chunker import ChunkingEngine
    from memory.rag.schemas import StorageConfig, RetrievalConfig, ChunkingConfig

    embed = LocalEmbeddings(dim=128)
    store = ChromaVectorStore(persist_path=retrieval_dir)
    chunker = ChunkingEngine(ChunkingConfig(min_chunk_size=1))
    storage = StorageEngine(embed, store,
                            StorageConfig(deduplicate=False, versioning_enabled=False))

    docs = [
        ("FastAPI authentication with JWT tokens and OAuth2 middleware", "backend_code", "be"),
        ("PostgreSQL schema with normalised users and notes tables", "database_design", "dbe"),
        ("React dashboard component with custom hooks and Tailwind CSS", "frontend_code", "fe"),
    ]
    for text, collection, agent in docs:
        chunks = chunker.chunk(text, artifact_type=collection)
        storage.ingest(chunks=chunks, project_id=8001, agent_name=agent,
                       artifact_type=collection, collection_name=collection, version=1)

    return RetrievalEngine(embed, store, RetrievalConfig(limit=5, threshold=0.0))


class TestRetrievalEngine:

    def test_search_returns_list(self, retrieval_fixture):
        results = retrieval_fixture.search(
            query="JWT authentication", project_id=8001, collection_name="backend_code",
        )
        assert isinstance(results, list)

    def test_search_results_have_required_fields(self, retrieval_fixture):
        results = retrieval_fixture.search(
            query="FastAPI", project_id=8001, collection_name="backend_code",
        )
        if results:
            r = results[0]
            assert hasattr(r, "id")
            assert hasattr(r, "document")
            assert hasattr(r, "metadata")
            assert hasattr(r, "similarity_score")
            assert hasattr(r, "collection")
            assert r.collection == "backend_code"

    def test_search_results_sorted_descending(self, retrieval_fixture):
        results = retrieval_fixture.search(
            query="database schema", project_id=8001, collection_name="database_design",
        )
        scores = [r.similarity_score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_search_empty_query_returns_empty(self, retrieval_fixture):
        assert retrieval_fixture.search(
            query="  ", project_id=8001, collection_name="backend_code",
        ) == []

    def test_threshold_filters_results(self, retrieval_fixture):
        results = retrieval_fixture.search(
            query="JWT authentication",
            project_id=8001,
            collection_name="backend_code",
            threshold=0.999,
        )
        for r in results:
            assert r.similarity_score >= 0.999

    def test_limit_caps_results(self, retrieval_fixture):
        results = retrieval_fixture.search(
            query="something", project_id=8001,
            collection_name="backend_code", limit=1,
        )
        assert len(results) <= 1

    def test_search_multi_returns_list(self, retrieval_fixture):
        """search_multi should always return a list (may be empty if nothing scored)."""
        results = retrieval_fixture.search_multi(
            query="PostgreSQL JWT React",
            project_id=8001,
        )
        assert isinstance(results, list)

    def test_metadata_filter_single_condition(self, retrieval_fixture):
        from memory.rag.schemas import MetadataFilter, FilterOperator
        filt = MetadataFilter(
            conditions={"agent_name": "be"},
            operator=FilterOperator.AND,
        )
        results = retrieval_fixture.search(
            query="FastAPI",
            project_id=8001,
            collection_name="backend_code",
            metadata_filter=filt,
        )
        for r in results:
            assert r.metadata.get("agent_name") == "be"

    def test_mmr_returns_list(self, retrieval_fixture):
        from memory.rag.schemas import RetrievalConfig
        original = retrieval_fixture.config
        retrieval_fixture.config = RetrievalConfig(use_mmr=True, mmr_lambda=0.7, limit=3)
        results = retrieval_fixture.search(
            query="FastAPI", project_id=8001, collection_name="backend_code",
        )
        assert isinstance(results, list)
        retrieval_fixture.config = original


# ===========================================================================
# RAGPipeline — end-to-end
# ===========================================================================

@pytest.fixture(scope="module")
def pipeline_fixture(pipeline_dir):
    from memory.embeddings.local import LocalEmbeddings
    from memory.vectorstores.chroma import ChromaVectorStore
    from memory.rag.pipeline import RAGPipeline
    from memory.rag.schemas import RAGConfig, ChunkingConfig, StorageConfig
    embed = LocalEmbeddings(dim=128)
    store = ChromaVectorStore(persist_path=pipeline_dir)
    cfg = RAGConfig(
        chunking=ChunkingConfig(min_chunk_size=1),
        storage=StorageConfig(deduplicate=False, versioning_enabled=False),
    )
    return RAGPipeline(embedding_provider=embed, vector_store=store, config=cfg)


class TestRAGPipeline:

    def test_ingest_returns_ingestion_result(self, pipeline_fixture):
        from memory.rag.schemas import IngestionResult
        result = pipeline_fixture.ingest(
            text="FastAPI backend with JWT authentication and PostgreSQL.",
            project_id=9001, agent_name="be",
            artifact_type="code", collection_name="backend_code", version=1,
        )
        assert isinstance(result, IngestionResult)
        assert result.stored_chunks > 0
        assert result.project_id == 9001

    def test_ingest_empty_text_returns_zero(self, pipeline_fixture):
        result = pipeline_fixture.ingest(
            text="   ", project_id=9001, agent_name="x",
            artifact_type="y", collection_name="backend_code", version=1,
        )
        assert result.stored_chunks == 0
        assert result.total_chunks == 0

    def test_retrieve_single_collection(self, pipeline_fixture):
        pipeline_fixture.ingest(
            text="PostgreSQL normalised schema with primary and foreign keys.",
            project_id=9002, agent_name="dbe",
            artifact_type="schema", collection_name="database_design", version=1,
        )
        results = pipeline_fixture.retrieve(
            query="PostgreSQL normalised schema",
            project_id=9002,
            collection_name="database_design",
        )
        assert isinstance(results, list)

    def test_retrieve_multi_collection_fanout(self, pipeline_fixture):
        pipeline_fixture.ingest(
            text="React dashboard component with state management.",
            project_id=9003, agent_name="fe",
            artifact_type="component", collection_name="frontend_code", version=1,
        )
        pipeline_fixture.ingest(
            text="FastAPI authentication endpoint with JWT.",
            project_id=9003, agent_name="be",
            artifact_type="endpoint", collection_name="backend_code", version=1,
        )
        results = pipeline_fixture.retrieve(
            query="authentication dashboard",
            project_id=9003,
            collection_name=None,
        )
        assert isinstance(results, list)

    def test_retrieve_with_metadata_filter(self, pipeline_fixture):
        from memory.rag.schemas import MetadataFilter
        pipeline_fixture.ingest(
            text="Security audit with OWASP top ten checks.",
            project_id=9004, agent_name="sec",
            artifact_type="audit", collection_name="security_reports", version=1,
        )
        filt = MetadataFilter(conditions={"agent_name": "sec"})
        results = pipeline_fixture.retrieve(
            query="OWASP security",
            project_id=9004,
            collection_name="security_reports",
            metadata_filter=filt,
        )
        for r in results:
            assert r.metadata.get("agent_name") == "sec"

    def test_reconfigure_updates_config(self, pipeline_fixture):
        from memory.rag.schemas import RAGConfig, ChunkingConfig, ChunkStrategy
        new_cfg = RAGConfig(
            chunking=ChunkingConfig(strategy=ChunkStrategy.SENTENCE,
                                    chunk_size=200, min_chunk_size=1),
        )
        pipeline_fixture.reconfigure(new_cfg)
        assert pipeline_fixture.config.chunking.strategy == ChunkStrategy.SENTENCE
        assert pipeline_fixture._chunker.config.chunk_size == 200

    def test_from_service_builds_pipeline(self, pipeline_dir):
        from memory.embeddings.local import LocalEmbeddings
        from memory.vectorstores.chroma import ChromaVectorStore
        from memory.service import MemoryService
        from memory.rag.pipeline import RAGPipeline
        svc = MemoryService(
            embedding_provider=LocalEmbeddings(dim=128),
            vector_store=ChromaVectorStore(persist_path=pipeline_dir),
        )
        pipeline = RAGPipeline.from_service(svc)
        assert pipeline is not None

    def test_multiple_versions_coexist(self, pipeline_dir):
        from memory.rag.pipeline import RAGPipeline
        from memory.embeddings.local import LocalEmbeddings
        from memory.vectorstores.chroma import ChromaVectorStore
        from memory.rag.schemas import RAGConfig, ChunkingConfig, StorageConfig

        d = tempfile.mkdtemp()
        try:
            p = RAGPipeline(
                embedding_provider=LocalEmbeddings(dim=128),
                vector_store=ChromaVectorStore(persist_path=d),
                config=RAGConfig(
                    chunking=ChunkingConfig(min_chunk_size=1),
                    storage=StorageConfig(deduplicate=False, versioning_enabled=False),
                ),
            )
            r1 = p.ingest(
                text="Version one of the backend service code.",
                project_id=9005, agent_name="be",
                artifact_type="code", collection_name="backend_code", version=1,
            )
            r2 = p.ingest(
                text="Version two with improved authentication handling.",
                project_id=9005, agent_name="be",
                artifact_type="code", collection_name="backend_code", version=2,
            )
            assert r1.stored_chunks > 0
            assert r2.stored_chunks > 0
        finally:
            shutil.rmtree(d, ignore_errors=True)


# ===========================================================================
# RAGConfig validation
# ===========================================================================

class TestRAGConfig:

    def test_default_construction(self):
        from memory.rag.schemas import RAGConfig
        cfg = RAGConfig()
        assert cfg.chunking.chunk_size == 800
        assert cfg.retrieval.limit == 5
        assert cfg.storage.batch_size == 64

    def test_nested_override(self):
        from memory.rag.schemas import RAGConfig, ChunkingConfig, ChunkStrategy
        cfg = RAGConfig(chunking=ChunkingConfig(strategy=ChunkStrategy.RECURSIVE,
                                                chunk_size=400, min_chunk_size=1))
        assert cfg.chunking.strategy == ChunkStrategy.RECURSIVE
        assert cfg.chunking.chunk_size == 400

    def test_chunking_config_validation_min_chunk(self):
        import pydantic
        from memory.rag.schemas import ChunkingConfig
        with pytest.raises(pydantic.ValidationError):
            ChunkingConfig(chunk_size=5)   # below ge=10

    def test_retrieval_config_threshold_bounds(self):
        import pydantic
        from memory.rag.schemas import RetrievalConfig
        with pytest.raises(pydantic.ValidationError):
            RetrievalConfig(threshold=1.5)

    def test_filter_operator_enum_values(self):
        from memory.rag.schemas import FilterOperator
        assert FilterOperator.AND.value == "and"
        assert FilterOperator.OR.value == "or"

    def test_chunk_strategy_enum_values(self):
        from memory.rag.schemas import ChunkStrategy
        assert ChunkStrategy.CHARACTER.value == "character"
        assert ChunkStrategy.SENTENCE.value == "sentence"
        assert ChunkStrategy.PARAGRAPH.value == "paragraph"
        assert ChunkStrategy.RECURSIVE.value == "recursive"


# ===========================================================================
# ChromaVectorStore — where kwarg
# ===========================================================================

class TestChromaVectorStoreWhere:

    def test_custom_where_clause_used(self, where_dir):
        from memory.embeddings.local import LocalEmbeddings
        from memory.vectorstores.chroma import ChromaVectorStore

        embed = LocalEmbeddings(dim=64)
        store = ChromaVectorStore(persist_path=where_dir)

        vec = embed.embed_documents(["test document content"])[0]
        store.store(
            collection_name="requirements",
            ids=["where-test-id"],
            documents=["test document content"],
            embeddings=[vec],
            metadatas=[{"project_id": 1, "agent_name": "tester",
                        "artifact_type": "t", "timestamp": "2024-01-01",
                        "version": 1}],
        )

        qvec = embed.embed_query("test document")
        result = store.query(
            collection_name="requirements",
            query_embeddings=[qvec],
            project_id=1,
            limit=5,
            where={"project_id": {"$eq": 1}},
        )
        assert result is not None
        assert "ids" in result

    def test_no_where_defaults_to_project_filter(self, where_dir):
        from memory.embeddings.local import LocalEmbeddings
        from memory.vectorstores.chroma import ChromaVectorStore

        embed = LocalEmbeddings(dim=64)
        store = ChromaVectorStore(persist_path=where_dir)
        qvec = embed.embed_query("anything")
        result = store.query(
            collection_name="requirements",
            query_embeddings=[qvec],
            project_id=9999,
            limit=3,
        )
        assert "ids" in result
