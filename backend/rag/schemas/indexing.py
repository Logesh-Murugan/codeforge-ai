"""
RAG Indexing Schemas — Phase 5.2

Pydantic data contracts for document ingestion and index management.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class IndexDocument(BaseModel):
    """A single document to be indexed in the RAG pipeline."""

    content: str = Field(
        ...,
        min_length=1,
        description="The text content to chunk, embed, and store.",
    )
    artifact_type: str = Field(
        default="document",
        description="Logical type label (e.g. 'requirements', 'code', 'architecture').",
    )
    agent_name: str = Field(
        default="system",
        description="Name of the agent or actor producing this document.",
    )
    version: int = Field(
        default=1,
        ge=1,
        description="Version number of the artifact.",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary key-value metadata stored alongside the embedding.",
    )


class IndexRequest(BaseModel):
    """Request to index a single document into a named collection."""

    project_id: int = Field(..., description="Owning project identifier.")
    collection: str = Field(
        ...,
        description="Target ChromaDB collection name.",
        examples=["requirements", "backend_code", "architecture"],
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Text content to chunk, embed, and persist.",
    )
    artifact_type: str = Field(
        default="document",
        description="Logical artifact type label.",
    )
    agent_name: str = Field(
        default="system",
        description="Agent or actor producing this document.",
    )
    version: int = Field(default=1, ge=1, description="Artifact version number.")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extra metadata merged with system-generated metadata.",
    )


class IndexBatchRequest(BaseModel):
    """Request to index multiple documents in one call."""

    project_id: int = Field(..., description="Owning project identifier.")
    collection: str = Field(
        ...,
        description="Target collection for all documents in this batch.",
    )
    documents: List[IndexDocument] = Field(
        ...,
        min_length=1,
        description="List of documents to index (max 50 per batch).",
    )


class IndexResult(BaseModel):
    """Result of a single document indexing operation."""

    memory_id: str = Field(
        ...,
        description="Memory ID of the first stored chunk (UUID).",
    )
    chunks_stored: int = Field(
        ...,
        description="Total number of chunks created and stored.",
    )
    collection: str = Field(..., description="Target collection used.")
    project_id: int = Field(..., description="Owning project identifier.")
    artifact_type: str = Field(..., description="Artifact type label used.")
    indexed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp of the indexing operation.",
    )


class IndexBatchResult(BaseModel):
    """Result of a batch indexing operation."""

    project_id: int
    collection: str
    total_documents: int = Field(..., description="Number of documents submitted.")
    total_chunks: int = Field(..., description="Total chunks stored across all documents.")
    results: List[IndexResult] = Field(..., description="Per-document results.")
    failed: int = Field(default=0, description="Number of documents that failed indexing.")
    indexed_at: datetime = Field(default_factory=datetime.utcnow)


class IndexStatus(BaseModel):
    """Snapshot of vector index state for a project."""

    project_id: int
    collections: Dict[str, int] = Field(
        ...,
        description="Mapping of collection name → document count.",
    )
    total_documents: int = Field(
        ...,
        description="Sum of documents across all collections.",
    )


class DeleteIndexResponse(BaseModel):
    """Response for index deletion operations."""

    message: str
    project_id: int
    collection: Optional[str] = Field(
        default=None,
        description="Specific collection deleted, or None if all were deleted.",
    )
