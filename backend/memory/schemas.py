"""
Memory subsystem Pydantic schemas.

All public data contracts for requests, responses, and internal
metadata are defined here.  No circular imports — this module imports
only from the standard library and Pydantic.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class ArtifactType(str, Enum):
    """
    Canonical artifact type identifiers for project memory records.

    These map to the functional categories produced by each agent in the
    CodeForge AI pipeline.
    """
    # Requirement phase
    REQUIREMENTS        = "requirements"
    # Architecture phase
    ARCHITECTURE        = "architecture"
    DATABASE_DESIGN     = "database_design"
    API_CONTRACTS       = "api_contracts"
    # Code generation
    BACKEND_CODE        = "backend_code"
    FRONTEND_CODE       = "frontend_code"
    # Assurance & ops
    SECURITY_REPORT     = "security_report"
    QA_REPORT           = "qa_report"
    DOCUMENTATION       = "documentation"
    DEVOPS              = "devops"
    # Meta
    CONVERSATION        = "conversation"
    PROJECT_HISTORY     = "project_history"
    # Generated file record (3.4)
    GENERATED_FILE      = "generated_file"
    # Agent memory (3.4)
    AGENT_OUTPUT        = "agent_output"
    # Revision (3.4)
    REVISION            = "revision"


class CollectionName(str, Enum):
    """Canonical collection identifiers used throughout the memory system."""
    REQUIREMENTS = "requirements"
    ARCHITECTURE = "architecture"
    DATABASE_DESIGN = "database_design"
    API_CONTRACTS = "api_contracts"
    BACKEND_CODE = "backend_code"
    FRONTEND_CODE = "frontend_code"
    SECURITY_REPORTS = "security_reports"
    QA_REPORTS = "qa_reports"
    DOCUMENTATION = "documentation"
    DEVOPS = "devops"
    CONVERSATION = "conversation"
    PROJECT_HISTORY = "project_history"


class EmbeddingProviderName(str, Enum):
    """Supported embedding provider identifiers."""
    LOCAL = "local"
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"


class MemoryMode(str, Enum):
    """Deployment mode: drives provider selection defaults."""
    LOCAL = "local"    # Ollama + ChromaDB
    CLOUD = "cloud"    # HuggingFace API + ChromaDB


# ---------------------------------------------------------------------------
# Memory metadata
# ---------------------------------------------------------------------------

class MemoryMetadata(BaseModel):
    """Flat metadata stored alongside every memory document in ChromaDB."""
    project_id: int
    agent_name: str
    artifact_type: str
    timestamp: str  # ISO-8601 UTC string — ChromaDB requires scalar values
    version: int


# ---------------------------------------------------------------------------
# Stored memory record
# ---------------------------------------------------------------------------

class MemoryRecord(BaseModel):
    """A single memory entry as returned by retrieval / listing operations."""
    id: str
    document: str
    metadata: MemoryMetadata
    similarity_score: Optional[float] = None  # populated by semantic search


# ---------------------------------------------------------------------------
# Query request / response
# ---------------------------------------------------------------------------

class MemoryQuery(BaseModel):
    """Input schema for a semantic memory search."""
    query: str = Field(..., min_length=1)
    limit: int = Field(default=5, ge=1, le=50)
    threshold: float = Field(default=0.0, ge=0.0, le=1.0)


class MemoryQueryResult(BaseModel):
    """Single hit returned by a semantic search query."""
    id: str
    document: str
    metadata: Dict[str, Any]
    similarity_score: float


# ---------------------------------------------------------------------------
# Store request
# ---------------------------------------------------------------------------

class MemoryStoreRequest(BaseModel):
    """Input schema for storing a new memory artifact."""
    project_id: int
    agent_name: str
    artifact_type: str
    collection_name: str
    content: str = Field(..., min_length=1)
    version: int = Field(default=1, ge=1)


# ---------------------------------------------------------------------------
# Chunk (RAG pipeline)
# ---------------------------------------------------------------------------

class TextChunk(BaseModel):
    """A single chunk produced by the text chunker."""
    chunk_index: int
    content: str
    char_start: int
    char_end: int
    source_artifact_type: str = ""


# ---------------------------------------------------------------------------
# Context injection
# ---------------------------------------------------------------------------

class AgentContext(BaseModel):
    """
    Assembled context block injected into an agent's system / user prompt.

    ``chunks`` is ordered by descending similarity score; the caller
    appends this to its prompt string.
    """
    project_id: int
    agent_name: str
    chunks: List[MemoryQueryResult] = Field(default_factory=list)
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)

    def to_prompt_block(self) -> str:
        """
        Render the context as a markdown-formatted string suitable for
        direct injection into an LLM prompt.
        """
        lines: List[str] = []

        if self.conversation_history:
            lines.append("### Previous Conversation")
            for turn in self.conversation_history:
                role = turn.get("role", "unknown").capitalize()
                content = turn.get("content", "")
                lines.append(f"**{role}:** {content}")
            lines.append("")

        if self.chunks:
            lines.append("### Relevant Project Memory")
            for i, chunk in enumerate(self.chunks, 1):
                score = f"{chunk.similarity_score:.2f}"
                lines.append(
                    f"[{i}] (score={score}) {chunk.document}"
                )

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Project history
# ---------------------------------------------------------------------------

class ProjectHistoryEntry(BaseModel):
    """A version-tracked snapshot of a project artifact."""
    id: str
    project_id: int
    agent_name: str
    artifact_type: str
    collection_name: str
    version: int
    content: str
    timestamp: datetime

    @classmethod
    def from_memory_record(cls, record: MemoryRecord) -> "ProjectHistoryEntry":
        meta = record.metadata
        return cls(
            id=record.id,
            project_id=meta.project_id,
            agent_name=meta.agent_name,
            artifact_type=meta.artifact_type,
            collection_name="project_history",
            version=meta.version,
            content=record.document,
            timestamp=datetime.fromisoformat(meta.timestamp),
        )


# ---------------------------------------------------------------------------
# Provider health status
# ---------------------------------------------------------------------------

class ProviderHealth(BaseModel):
    """Health status of an embedding provider."""
    provider_name: str
    healthy: bool
    dimension: Optional[int] = None
    error: Optional[str] = None
    checked_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


# ---------------------------------------------------------------------------
# Phase 3.4 — Project Memory schemas
# ---------------------------------------------------------------------------

class AgentMemoryRecord(BaseModel):
    """
    A versioned output record produced by one agent for one project.

    Stored in the agent's canonical collection *and* mirrored into
    ``project_history`` by ``ProjectMemoryService``.
    """
    id: str
    project_id: int
    agent_name: str
    artifact_type: str
    collection_name: str
    content: str
    version: int
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GeneratedFileRecord(BaseModel):
    """
    Represents a single file that was generated for a project.

    ``file_path`` is relative to the project root (e.g. ``backend/main.py``).
    ``language`` is a hint for syntax highlighting / processing.
    """
    id: str
    project_id: int
    file_path: str
    language: str
    content: str
    agent_name: str
    version: int
    timestamp: datetime


class RevisionEntry(BaseModel):
    """
    A tracked revision of any project artifact.

    A revision differs from a version in that it records *why* the change
    was made (``reason``) and who requested it (``requested_by``).
    """
    id: str
    project_id: int
    artifact_type: str
    version: int
    content: str
    reason: str = ""
    requested_by: str = "system"
    timestamp: datetime


class ProjectSnapshot(BaseModel):
    """
    A full point-in-time snapshot of everything recorded for a project.

    Returned by ``ProjectMemoryService.get_project_snapshot()``.
    """
    project_id: int
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    requirements: List[AgentMemoryRecord] = Field(default_factory=list)
    architecture: List[AgentMemoryRecord] = Field(default_factory=list)
    generated_files: List[GeneratedFileRecord] = Field(default_factory=list)
    agent_outputs: List[AgentMemoryRecord] = Field(default_factory=list)
    revisions: List[RevisionEntry] = Field(default_factory=list)
    version_history: List["ProjectHistoryEntry"] = Field(default_factory=list)

    @property
    def total_artifacts(self) -> int:
        return (
            len(self.requirements)
            + len(self.architecture)
            + len(self.generated_files)
            + len(self.agent_outputs)
        )


# ---------------------------------------------------------------------------
# Phase 3.4 — Store/Query request schemas for the memory API
# ---------------------------------------------------------------------------

class StoreArtifactRequest(BaseModel):
    """Request body for POST /projects/{id}/memory/artifacts."""
    agent_name: str = Field(..., min_length=1)
    artifact_type: str = Field(..., min_length=1)
    collection_name: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    version: int = Field(default=1, ge=1)
    file_path: Optional[str] = None
    language: Optional[str] = None


class StoreRevisionRequest(BaseModel):
    """Request body for POST /projects/{id}/memory/revisions."""
    artifact_type: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    version: int = Field(default=1, ge=1)
    reason: str = Field(default="")
    requested_by: str = Field(default="system")


class VersionHistoryQuery(BaseModel):
    """Query parameters for GET /projects/{id}/memory/versions."""
    artifact_type: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)


class MemorySearchRequest(BaseModel):
    """Request body for POST /projects/{id}/memory/search."""
    query: str = Field(..., min_length=1)
    collections: Optional[List[str]] = None
    limit: int = Field(default=5, ge=1, le=50)
    threshold: float = Field(default=0.0, ge=0.0, le=1.0)


