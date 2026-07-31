"""
ContextBuilderService — Phase 5.2

Assembles a prompt-ready context block for agent injection by:

  1. Querying multiple ChromaDB collections for the most relevant chunks
  2. Globally ranking all chunks by cosine similarity
  3. Truncating to MAX_CHUNKS and MAX_CHARS
  4. Optionally appending recent conversation history
  5. Formatting a clean, structured ``context_text`` string

The resulting ``ContextBlock.context_text`` can be prepended to any
agent prompt to ground the agent in project-relevant memory.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional

from rag.config import rag_settings
from rag.schemas.context import (
    ContextBlock,
    ContextChunk,
    ContextRequest,
    ContextResponse,
    ConversationTurn,
)

logger = logging.getLogger(__name__)


def _format_context_text(
    chunks: List[ContextChunk],
    conversation: List[ConversationTurn],
    query: str,
    agent_name: str,
) -> str:
    """
    Format a list of context chunks into a human-readable injection block.

    Produces a structured markdown-style block suitable for prepending to
    any agent prompt.
    """
    lines: List[str] = [
        f"# Context for {agent_name}",
        f"## Query: {query}",
        "",
    ]

    if chunks:
        lines.append("## Relevant Memory")
        for i, chunk in enumerate(chunks, 1):
            source = chunk.source_collection.replace("_", " ").title()
            score = f"{chunk.similarity_score:.3f}"
            artifact = f" [{chunk.artifact_type}]" if chunk.artifact_type else ""
            lines.append(f"\n### [{i}] {source}{artifact} (similarity: {score})")
            lines.append(chunk.content.strip())

    if conversation:
        lines.append("\n## Recent Conversation")
        for turn in conversation:
            role = turn.role.upper()
            lines.append(f"**{role}**: {turn.content.strip()}")

    return "\n".join(lines)


class ContextBuilderService:
    """
    Context assembly service for the RAG pipeline.

    Args:
        memory_service: Optional injected MemoryService for testing.
                        When None, resolved from ``memory.manager.default_manager``.
    """

    def __init__(self, memory_service=None) -> None:
        self._memory_service = memory_service

    # ── Private helpers ─────────────────────────────────────────────────

    def _get_service(self):
        if self._memory_service is not None:
            return self._memory_service
        from memory.manager import default_manager
        return default_manager.get_service()

    def _resolve_collections(self, collections: Optional[List[str]]) -> List[str]:
        if collections:
            known = set(rag_settings.get_collections())
            valid = [c for c in collections if c in known]
            return valid or rag_settings.get_search_collections()
        return rag_settings.get_search_collections()

    # ── Public API ───────────────────────────────────────────────────────

    async def build_context(self, request: ContextRequest) -> ContextResponse:
        """
        Build a fully assembled, prompt-ready context block.

        Searches the requested collections for relevant chunks, globally
        ranks them by cosine similarity, truncates to the configured limits,
        and formats a ``context_text`` string ready for prompt injection.

        Args:
            request: Validated ContextRequest.

        Returns:
            ContextResponse with the assembled ContextBlock.
        """
        svc = self._get_service()
        collections = self._resolve_collections(request.collections)

        logger.info(
            "[RAG-CONTEXT] Building context for agent=%s project=%d "
            "query='%s' collections=%s limit=%d threshold=%.2f",
            request.agent_name,
            request.project_id,
            request.query[:80],
            collections,
            request.limit,
            request.threshold,
        )

        # ── Step 1: Retrieve chunks from each collection ──────────────────
        raw_chunks: List[ContextChunk] = []

        for col in collections:
            try:
                results = svc.retrieve_memory(
                    project_id=request.project_id,
                    collection_name=col,
                    query=request.query,
                    limit=request.limit,
                    threshold=request.threshold,
                )
                for r in results:
                    meta = r.get("metadata", {})
                    raw_chunks.append(
                        ContextChunk(
                            content=r["document"],
                            source_collection=col,
                            similarity_score=r["similarity_score"],
                            metadata=meta,
                            artifact_type=meta.get("artifact_type"),
                            agent_name=meta.get("agent_name"),
                            chunk_index=meta.get("chunk_index"),
                        )
                    )
            except Exception as exc:
                logger.debug(
                    "[RAG-CONTEXT] Skipping collection '%s': %s", col, exc
                )

        # ── Step 2: Global rank by similarity ────────────────────────────
        raw_chunks.sort(key=lambda c: c.similarity_score, reverse=True)

        # ── Step 3: Deduplicate by content (avoid duplicate chunks) ──────
        seen_content: set = set()
        unique_chunks: List[ContextChunk] = []
        for chunk in raw_chunks:
            key = chunk.content[:200]  # compare first 200 chars as fingerprint
            if key not in seen_content:
                seen_content.add(key)
                unique_chunks.append(chunk)

        # ── Step 4: Apply limit ──────────────────────────────────────────
        max_chunks = min(request.limit, rag_settings.RAG_CONTEXT_MAX_CHUNKS)
        selected = unique_chunks[:max_chunks]

        # ── Step 5: Apply character budget ──────────────────────────────
        budget = rag_settings.RAG_CONTEXT_MAX_CHARS
        budget_chunks: List[ContextChunk] = []
        used_chars = 0
        for chunk in selected:
            needed = len(chunk.content)
            if used_chars + needed > budget:
                # Truncate last chunk to fit within budget
                remaining = budget - used_chars
                if remaining > 50:  # only include if meaningful
                    truncated = ContextChunk(
                        content=chunk.content[:remaining] + "…",
                        source_collection=chunk.source_collection,
                        similarity_score=chunk.similarity_score,
                        metadata=chunk.metadata,
                        artifact_type=chunk.artifact_type,
                        agent_name=chunk.agent_name,
                        chunk_index=chunk.chunk_index,
                    )
                    budget_chunks.append(truncated)
                break
            budget_chunks.append(chunk)
            used_chars += needed

        # ── Step 6: Fetch conversation history (optional) ────────────────
        conversation: List[ConversationTurn] = []
        if request.include_conversation:
            try:
                raw_conv = svc.get_conversation_history(
                    project_id=request.project_id,
                    limit=request.conversation_limit,
                )
                conversation = [
                    ConversationTurn(role=t["role"], content=t["content"])
                    for t in raw_conv
                ]
            except Exception as exc:
                logger.debug("[RAG-CONTEXT] Conversation history unavailable: %s", exc)

        # ── Step 7: Format context text ──────────────────────────────────
        context_text = _format_context_text(
            chunks=budget_chunks,
            conversation=conversation,
            query=request.query,
            agent_name=request.agent_name,
        )

        logger.info(
            "[RAG-CONTEXT] Built context: %d chunk(s), %d conv turns, %d chars",
            len(budget_chunks),
            len(conversation),
            len(context_text),
        )

        block = ContextBlock(
            project_id=request.project_id,
            agent_name=request.agent_name,
            query=request.query,
            chunks=budget_chunks,
            conversation_history=conversation,
            context_text=context_text,
            total_chunks=len(budget_chunks),
            collections_searched=collections,
            built_at=datetime.now(timezone.utc),
        )

        return ContextResponse(
            project_id=request.project_id,
            agent_name=request.agent_name,
            query=request.query,
            context=block,
            total_chunks=len(budget_chunks),
            collections_searched=collections,
        )
