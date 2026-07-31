"""
RAG Context Schemas — Phase 5.2

Pydantic data contracts for agent context assembly.
Context blocks are prompt-ready representations of the most relevant
memory chunks for a given query, across multiple collections.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ContextRequest(BaseModel):
    """Request to build a context block for an agent prompt."""

    project_id: int = Field(..., description="Owning project identifier.")
    agent_name: str = Field(
        ...,
        description="Name of the agent that will consume this context.",
    )
    query: str = Field(
        ...,
        min_length=1,
        description="Natural-language query used to retrieve relevant chunks.",
    )
    collections: Optional[List[str]] = Field(
        default=None,
        description=(
            "Collections to search. Defaults to all semantic collections "
            "(excludes 'conversation', 'project_history')."
        ),
    )
    limit: int = Field(
        default=8,
        ge=1,
        le=50,
        description="Maximum number of chunks to include in the context block.",
    )
    threshold: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score for chunks to be included.",
    )
    include_conversation: bool = Field(
        default=False,
        description="Whether to append recent conversation history to the context.",
    )
    conversation_limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Max conversation turns to include when include_conversation=True.",
    )


class ContextChunk(BaseModel):
    """A single memory chunk included in a context block."""

    content: str = Field(..., description="Text content of the chunk.")
    source_collection: str = Field(..., description="Collection the chunk came from.")
    similarity_score: float = Field(
        ...,
        description="Cosine similarity between the query and this chunk.",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Original metadata stored with this chunk.",
    )
    artifact_type: Optional[str] = Field(
        default=None,
        description="Extracted artifact_type from metadata (convenience field).",
    )
    agent_name: Optional[str] = Field(
        default=None,
        description="Extracted agent_name from metadata (convenience field).",
    )
    chunk_index: Optional[int] = Field(
        default=None,
        description="Chunk index within the original document.",
    )


class ConversationTurn(BaseModel):
    """A single conversation turn stored in the context."""

    role: str = Field(..., description="'user' | 'assistant' | 'system'.")
    content: str = Field(..., description="Turn text content.")


class ContextBlock(BaseModel):
    """
    A fully assembled, prompt-ready context block for agent injection.

    ``context_text`` is the formatted string ready to be prepended to
    an agent prompt. Individual chunks are also available for inspection.
    """

    project_id: int
    agent_name: str
    query: str
    chunks: List[ContextChunk] = Field(
        ...,
        description="Ranked memory chunks included in the context.",
    )
    conversation_history: List[ConversationTurn] = Field(
        default_factory=list,
        description="Recent conversation turns (if requested).",
    )
    context_text: str = Field(
        ...,
        description="Formatted context string ready for prompt injection.",
    )
    total_chunks: int
    collections_searched: List[str]
    built_at: datetime = Field(default_factory=datetime.utcnow)


class ContextResponse(BaseModel):
    """HTTP response wrapper for context assembly."""

    project_id: int
    agent_name: str
    query: str
    context: ContextBlock
    total_chunks: int
    collections_searched: List[str]
