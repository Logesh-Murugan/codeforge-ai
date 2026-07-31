"""
RAG Retrieval Schemas — Phase 5.2

Pydantic data contracts for semantic search, similarity retrieval,
project document listing, and system health.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Request for semantic search across one or more collections."""

    project_id: int = Field(..., description="Owning project identifier.")
    query: str = Field(
        ...,
        min_length=1,
        description="Natural-language search query.",
    )
    collections: Optional[List[str]] = Field(
        default=None,
        description=(
            "Collections to search. Defaults to all non-meta collections "
            "(excludes 'conversation', 'project_history')."
        ),
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Maximum number of results to return (per collection).",
    )
    threshold: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity score for results.",
    )


class SearchResult(BaseModel):
    """A single result returned from semantic search."""

    id: str = Field(..., description="ChromaDB document ID (UUID).")
    document: str = Field(..., description="The text content of the matched chunk.")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata stored alongside the embedding.",
    )
    similarity_score: float = Field(
        ...,
        description="Cosine similarity score between query and document (0.0–1.0).",
    )
    collection: str = Field(..., description="Source collection the result came from.")


class SearchResponse(BaseModel):
    """Full response for a semantic search query."""

    project_id: int
    query: str
    results: List[SearchResult]
    total: int = Field(..., description="Total number of results returned.")
    collections_searched: List[str] = Field(
        ...,
        description="Names of all collections that were queried.",
    )


class SimilarityRequest(BaseModel):
    """Request for similarity search within a single named collection."""

    project_id: int = Field(..., description="Owning project identifier.")
    query: str = Field(
        ...,
        min_length=1,
        description="Text to find similar documents for.",
    )
    collection: str = Field(
        ...,
        description="Target collection to search within.",
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Maximum number of similar documents to return.",
    )
    threshold: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score filter.",
    )


class SimilarityResult(BaseModel):
    """A single similarity search result."""

    id: str
    document: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    similarity_score: float
    collection: str


class SimilarityResponse(BaseModel):
    """Full response for a similarity search query."""

    project_id: int
    query: str
    collection: str
    results: List[SimilarityResult]
    total: int


class DocumentRecord(BaseModel):
    """A raw document stored in a collection."""

    id: str = Field(..., description="ChromaDB document ID.")
    document: str = Field(..., description="Raw text content.")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    collection: str


class ProjectDocumentsResponse(BaseModel):
    """All documents stored for a project within a collection."""

    project_id: int
    collection: str
    documents: List[DocumentRecord]
    total: int


class CollectionsResponse(BaseModel):
    """List of all available RAG collection names."""

    collections: List[str]
    total: int


class HealthResponse(BaseModel):
    """RAG engine health and active embedding provider information."""

    status: str = Field(..., description="'healthy' or 'degraded'.")
    embedding_provider: str = Field(
        ...,
        description="Active embedding provider name (ollama / huggingface / local).",
    )
    embedding_dimension: int = Field(
        ...,
        description="Dimension of vectors produced by the active provider.",
    )
    provider_healthy: bool = Field(
        ...,
        description="Whether the active embedding provider passed its health check.",
    )
    mode: str = Field(
        ...,
        description="Resolved mode: 'local' (Ollama), 'cloud' (HuggingFace), or 'fallback'.",
    )
    detail: Optional[str] = Field(
        default=None,
        description="Optional error detail when provider is unhealthy.",
    )
