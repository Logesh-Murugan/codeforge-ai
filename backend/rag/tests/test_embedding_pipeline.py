"""
Tests for Phase 5.2 — EmbeddingPipelineService (Unit Tests)

All tests use a mocked MemoryService — no live DB, Ollama, or ChromaDB required.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from rag.schemas.indexing import IndexRequest, IndexBatchRequest, IndexDocument
from rag.services.embedding_pipeline import EmbeddingPipelineService


# ── Fixtures ─────────────────────────────────────────────────────────────────

def _make_mock_service(memory_id: str = "test-uuid-1234") -> MagicMock:
    """Return a mock MemoryService with store_memory stubbed."""
    svc = MagicMock()
    svc.store_memory.return_value = memory_id
    return svc


def _make_index_request(**kwargs) -> IndexRequest:
    defaults = {
        "project_id": 42,
        "collection": "requirements",
        "content": "This is a test document for the RAG pipeline.",
        "artifact_type": "requirements",
        "agent_name": "system",
        "version": 1,
        "metadata": {},
    }
    defaults.update(kwargs)
    return IndexRequest(**defaults)


# ── EmbeddingPipelineService — ingest ────────────────────────────────────────

class TestIngest:
    """Tests for EmbeddingPipelineService.ingest()."""

    @pytest.mark.asyncio
    async def test_ingest_returns_index_result(self):
        """A valid request produces an IndexResult with correct fields."""
        mock_svc = _make_mock_service("abc-123")
        pipeline = EmbeddingPipelineService(memory_service=mock_svc)
        req = _make_index_request()

        result = await pipeline.ingest(req)

        assert result.memory_id == "abc-123"
        assert result.collection == "requirements"
        assert result.project_id == 42
        assert result.artifact_type == "requirements"
        assert result.chunks_stored >= 1

    @pytest.mark.asyncio
    async def test_ingest_calls_store_memory_with_correct_args(self):
        """store_memory is called with project_id, agent_name, artifact_type, collection."""
        mock_svc = _make_mock_service()
        pipeline = EmbeddingPipelineService(memory_service=mock_svc)
        req = _make_index_request(
            project_id=99,
            collection="backend_code",
            artifact_type="code",
            agent_name="backend_agent",
            version=3,
        )

        await pipeline.ingest(req)

        mock_svc.store_memory.assert_called_once_with(
            project_id=99,
            agent_name="backend_agent",
            artifact_type="code",
            collection_name="backend_code",
            content=req.content,
            version=3,
        )

    @pytest.mark.asyncio
    async def test_ingest_raises_on_empty_content(self):
        """Empty content (after strip) raises ValueError."""
        mock_svc = _make_mock_service()
        pipeline = EmbeddingPipelineService(memory_service=mock_svc)
        req = _make_index_request(content="   ")

        with pytest.raises(ValueError, match="Content must not be empty"):
            await pipeline.ingest(req)

    @pytest.mark.asyncio
    async def test_ingest_strips_whitespace_before_store(self):
        """Leading/trailing whitespace is stripped from content before storage."""
        mock_svc = _make_mock_service()
        pipeline = EmbeddingPipelineService(memory_service=mock_svc)
        req = _make_index_request(content="  Hello World  ")

        await pipeline.ingest(req)

        call_args = mock_svc.store_memory.call_args
        assert call_args.kwargs["content"] == "Hello World"

    @pytest.mark.asyncio
    async def test_ingest_propagates_store_memory_error(self):
        """RuntimeError from store_memory propagates to the caller."""
        mock_svc = MagicMock()
        mock_svc.store_memory.side_effect = RuntimeError("Embedding server down")
        pipeline = EmbeddingPipelineService(memory_service=mock_svc)
        req = _make_index_request()

        with pytest.raises(RuntimeError, match="Embedding server down"):
            await pipeline.ingest(req)

    @pytest.mark.asyncio
    async def test_ingest_short_content_is_one_chunk(self):
        """Content shorter than RAG_CHUNK_SIZE results in chunks_stored == 1."""
        mock_svc = _make_mock_service()
        pipeline = EmbeddingPipelineService(memory_service=mock_svc)
        req = _make_index_request(content="Short text.")

        result = await pipeline.ingest(req)

        assert result.chunks_stored == 1

    @pytest.mark.asyncio
    async def test_ingest_result_has_indexed_at_timestamp(self):
        """IndexResult.indexed_at is a non-None datetime."""
        from datetime import datetime
        mock_svc = _make_mock_service()
        pipeline = EmbeddingPipelineService(memory_service=mock_svc)
        result = await pipeline.ingest(_make_index_request())

        assert result.indexed_at is not None
        assert isinstance(result.indexed_at, datetime)


# ── EmbeddingPipelineService — ingest_batch ───────────────────────────────────

class TestIngestBatch:
    """Tests for EmbeddingPipelineService.ingest_batch()."""

    def _make_batch_request(self, n: int = 3) -> IndexBatchRequest:
        docs = [
            IndexDocument(
                content=f"Document number {i} for batch ingestion testing.",
                artifact_type="requirements",
                agent_name="system",
                version=1,
            )
            for i in range(n)
        ]
        return IndexBatchRequest(
            project_id=42,
            collection="requirements",
            documents=docs,
        )

    @pytest.mark.asyncio
    async def test_batch_returns_all_results(self):
        """Batch result contains one IndexResult per document."""
        mock_svc = _make_mock_service()
        pipeline = EmbeddingPipelineService(memory_service=mock_svc)
        req = self._make_batch_request(n=3)

        result = await pipeline.ingest_batch(req)

        assert result.total_documents == 3
        assert len(result.results) == 3
        assert result.failed == 0

    @pytest.mark.asyncio
    async def test_batch_counts_total_chunks(self):
        """total_chunks is the sum of chunks across all documents."""
        mock_svc = _make_mock_service()
        pipeline = EmbeddingPipelineService(memory_service=mock_svc)
        req = self._make_batch_request(n=2)

        result = await pipeline.ingest_batch(req)

        assert result.total_chunks >= 2  # at least 1 chunk per doc

    @pytest.mark.asyncio
    async def test_batch_counts_failures(self):
        """Failed documents are counted without aborting the batch."""
        call_count = 0

        def failing_store(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise RuntimeError("Simulated failure on doc 2")
            return "ok-id"

        mock_svc = MagicMock()
        mock_svc.store_memory.side_effect = failing_store
        pipeline = EmbeddingPipelineService(memory_service=mock_svc)
        req = self._make_batch_request(n=3)

        result = await pipeline.ingest_batch(req)

        assert result.failed == 1
        assert len(result.results) == 2

    @pytest.mark.asyncio
    async def test_batch_empty_documents_list_raises(self):
        """A batch with no documents should fail Pydantic validation."""
        with pytest.raises(Exception):  # Pydantic min_length=1
            IndexBatchRequest(project_id=1, collection="requirements", documents=[])

    @pytest.mark.asyncio
    async def test_batch_result_has_project_id_and_collection(self):
        """Batch result echoes project_id and collection."""
        mock_svc = _make_mock_service()
        pipeline = EmbeddingPipelineService(memory_service=mock_svc)
        req = self._make_batch_request(n=1)

        result = await pipeline.ingest_batch(req)

        assert result.project_id == 42
        assert result.collection == "requirements"


# ── _count_chunks helper ─────────────────────────────────────────────────────

class TestCountChunks:
    """Tests for the internal chunk estimation helper."""

    def test_empty_content_is_zero_chunks(self):
        count = EmbeddingPipelineService._count_chunks("", 800, 100)
        assert count == 0

    def test_short_content_is_one_chunk(self):
        count = EmbeddingPipelineService._count_chunks("hello", 800, 100)
        assert count == 1

    def test_content_at_boundary_is_one_chunk(self):
        count = EmbeddingPipelineService._count_chunks("x" * 800, 800, 100)
        assert count == 1

    def test_long_content_is_multiple_chunks(self):
        count = EmbeddingPipelineService._count_chunks("x" * 1600, 800, 100)
        assert count >= 2
