"""
Tests for Phase 5.2 — ContextBuilderService (Unit Tests)

All tests use a mocked MemoryService — no live DB, Ollama, or ChromaDB required.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from rag.schemas.context import ContextRequest
from rag.services.context_builder import ContextBuilderService, _format_context_text


# ── Fixtures ─────────────────────────────────────────────────────────────────

def _raw_result(
    doc: str = "The system uses JWT authentication.",
    score: float = 0.85,
    artifact_type: str = "requirements",
    chunk_index: int = 0,
):
    return {
        "id": f"uuid-{hash(doc) % 10000}",
        "document": doc,
        "metadata": {
            "project_id": 42,
            "artifact_type": artifact_type,
            "agent_name": "system",
            "chunk_index": chunk_index,
        },
        "similarity_score": score,
    }


def _make_mock_service(results=None, conv_history=None):
    svc = MagicMock()
    svc.retrieve_memory.return_value = results if results is not None else [_raw_result()]
    svc.get_conversation_history.return_value = (
        conv_history if conv_history is not None else []
    )
    return svc


def _make_context_request(**kwargs):
    defaults = {
        "project_id": 42,
        "agent_name": "backend_agent",
        "query": "How does authentication work?",
        "collections": ["requirements"],
        "limit": 5,
        "threshold": 0.0,
        "include_conversation": False,
    }
    defaults.update(kwargs)
    return ContextRequest(**defaults)


# ── ContextBuilderService — build_context ────────────────────────────────────

class TestBuildContext:
    """Tests for ContextBuilderService.build_context()."""

    @pytest.mark.asyncio
    async def test_build_context_returns_response(self):
        """build_context returns a ContextResponse with correct structure."""
        svc = ContextBuilderService(memory_service=_make_mock_service())
        resp = await svc.build_context(_make_context_request())

        assert resp.project_id == 42
        assert resp.agent_name == "backend_agent"
        assert resp.query == "How does authentication work?"
        assert resp.total_chunks >= 1
        assert resp.context is not None

    @pytest.mark.asyncio
    async def test_context_block_has_context_text(self):
        """The assembled context_text is a non-empty string."""
        svc = ContextBuilderService(memory_service=_make_mock_service())
        resp = await svc.build_context(_make_context_request())

        assert len(resp.context.context_text) > 0

    @pytest.mark.asyncio
    async def test_context_text_contains_query(self):
        """context_text includes the original query."""
        svc = ContextBuilderService(memory_service=_make_mock_service())
        resp = await svc.build_context(_make_context_request())

        assert "How does authentication work?" in resp.context.context_text

    @pytest.mark.asyncio
    async def test_context_text_contains_agent_name(self):
        """context_text contains the agent name in the header."""
        svc = ContextBuilderService(memory_service=_make_mock_service())
        resp = await svc.build_context(_make_context_request(agent_name="security_agent"))

        assert "security_agent" in resp.context.context_text

    @pytest.mark.asyncio
    async def test_context_text_contains_chunk_content(self):
        """Chunk content is embedded in the context_text."""
        svc = ContextBuilderService(
            memory_service=_make_mock_service(
                results=[_raw_result(doc="JWT tokens are used for sessions.")]
            )
        )
        resp = await svc.build_context(_make_context_request())

        assert "JWT tokens are used for sessions." in resp.context.context_text

    @pytest.mark.asyncio
    async def test_chunks_sorted_by_similarity_desc(self):
        """Chunks in the context block are sorted highest similarity first."""
        results = [
            _raw_result(doc=f"Doc {i}", score=score)
            for i, score in enumerate([0.3, 0.9, 0.6])
        ]
        # Assign unique ids
        for i, r in enumerate(results):
            r["id"] = f"id-{i}"
        svc = ContextBuilderService(memory_service=_make_mock_service(results=results))
        resp = await svc.build_context(_make_context_request())

        scores = [c.similarity_score for c in resp.context.chunks]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_empty_results_produces_empty_context(self):
        """Zero results produces a valid (but chunk-empty) context."""
        svc = ContextBuilderService(memory_service=_make_mock_service(results=[]))
        resp = await svc.build_context(_make_context_request())

        assert resp.total_chunks == 0
        assert resp.context.chunks == []
        assert "How does authentication work?" in resp.context.context_text

    @pytest.mark.asyncio
    async def test_collections_searched_in_response(self):
        """ContextResponse.collections_searched echoes queried collections."""
        svc = ContextBuilderService(memory_service=_make_mock_service(results=[]))
        resp = await svc.build_context(
            _make_context_request(collections=["requirements", "architecture"])
        )

        assert "requirements" in resp.collections_searched
        assert "architecture" in resp.collections_searched

    @pytest.mark.asyncio
    async def test_failing_collection_is_skipped(self):
        """A collection that raises does not abort context assembly."""
        mock_svc = MagicMock()
        mock_svc.retrieve_memory.side_effect = RuntimeError("Store unavailable")
        mock_svc.get_conversation_history.return_value = []
        svc = ContextBuilderService(memory_service=mock_svc)
        resp = await svc.build_context(_make_context_request())

        assert resp.total_chunks == 0  # graceful empty


# ── Conversation history ──────────────────────────────────────────────────────

class TestConversationHistory:
    """Tests for conversation history inclusion in context."""

    @pytest.mark.asyncio
    async def test_conversation_included_when_requested(self):
        """Conversation history appears in context_text when include_conversation=True."""
        conv = [
            {"role": "user", "content": "What is the auth method?"},
            {"role": "assistant", "content": "We use JWT."},
        ]
        svc = ContextBuilderService(
            memory_service=_make_mock_service(results=[], conv_history=conv)
        )
        resp = await svc.build_context(
            _make_context_request(include_conversation=True)
        )

        assert "What is the auth method?" in resp.context.context_text
        assert "We use JWT." in resp.context.context_text

    @pytest.mark.asyncio
    async def test_conversation_excluded_by_default(self):
        """Conversation history is NOT included when include_conversation=False."""
        conv = [{"role": "user", "content": "Private conversation turn"}]
        svc = ContextBuilderService(
            memory_service=_make_mock_service(results=[], conv_history=conv)
        )
        resp = await svc.build_context(
            _make_context_request(include_conversation=False)
        )

        assert "Private conversation turn" not in resp.context.context_text

    @pytest.mark.asyncio
    async def test_conversation_history_failure_is_silent(self):
        """Failure fetching conversation history does not raise."""
        mock_svc = _make_mock_service(results=[])
        mock_svc.get_conversation_history.side_effect = RuntimeError("Conv error")
        svc = ContextBuilderService(memory_service=mock_svc)
        resp = await svc.build_context(
            _make_context_request(include_conversation=True)
        )

        assert resp.context.conversation_history == []


# ── Deduplication ─────────────────────────────────────────────────────────────

class TestDeduplication:
    """Tests for chunk deduplication in context assembly."""

    @pytest.mark.asyncio
    async def test_duplicate_chunks_deduplicated(self):
        """Chunks with identical content are deduplicated."""
        same_doc = "This content appears twice."
        results = [_raw_result(doc=same_doc), _raw_result(doc=same_doc)]
        results[0]["id"] = "id-A"
        results[1]["id"] = "id-B"
        svc = ContextBuilderService(memory_service=_make_mock_service(results=results))
        resp = await svc.build_context(_make_context_request())

        contents = [c.content for c in resp.context.chunks]
        assert contents.count(same_doc) == 1


# ── _format_context_text helper ───────────────────────────────────────────────

class TestFormatContextText:
    """Tests for the internal context text formatter."""

    def test_header_contains_agent_name(self):
        from rag.schemas.context import ContextChunk, ConversationTurn
        chunk = ContextChunk(
            content="Test chunk",
            source_collection="requirements",
            similarity_score=0.85,
        )
        result = _format_context_text(
            chunks=[chunk],
            conversation=[],
            query="test query",
            agent_name="test_agent",
        )
        assert "test_agent" in result

    def test_chunks_section_present(self):
        from rag.schemas.context import ContextChunk
        chunk = ContextChunk(
            content="Relevant content here.",
            source_collection="architecture",
            similarity_score=0.7,
        )
        result = _format_context_text(
            chunks=[chunk],
            conversation=[],
            query="q",
            agent_name="agent",
        )
        assert "Relevant Memory" in result
        assert "Relevant content here." in result

    def test_empty_chunks_no_relevant_memory_section(self):
        result = _format_context_text(
            chunks=[],
            conversation=[],
            query="q",
            agent_name="agent",
        )
        assert "Relevant Memory" not in result

    def test_conversation_section_present_when_provided(self):
        from rag.schemas.context import ConversationTurn
        turns = [ConversationTurn(role="user", content="Hello")]
        result = _format_context_text(
            chunks=[],
            conversation=turns,
            query="q",
            agent_name="agent",
        )
        assert "Recent Conversation" in result
        assert "Hello" in result
