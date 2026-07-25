"""
RAG Pipeline Pydantic schemas — Phase 3.3.

All data contracts that are specific to the RAG pipeline layer live here.
General memory contracts stay in ``memory.schemas``.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class ChunkStrategy(str, Enum):
    """Text splitting strategy for the chunking engine."""
    CHARACTER  = "character"   # fixed-size character windows  (default)
    SENTENCE   = "sentence"    # split on sentence boundaries first
    PARAGRAPH  = "paragraph"   # split on blank lines / paragraph breaks
    RECURSIVE  = "recursive"   # try paragraph → sentence → character


class FilterOperator(str, Enum):
    """Logical operator for combining MetadataFilter clauses."""
    AND = "and"
    OR  = "or"


# ---------------------------------------------------------------------------
# Configuration objects (all fields have safe defaults so callers can
# construct them with zero arguments and override only what they need)
# ---------------------------------------------------------------------------

class ChunkingConfig(BaseModel):
    """Configuration for ChunkingEngine."""

    strategy: ChunkStrategy = ChunkStrategy.CHARACTER
    chunk_size: int = Field(default=800, ge=10, le=8000,
                            description="Maximum characters per chunk.")
    overlap: int = Field(default=100, ge=0,
                         description="Shared characters between adjacent chunks.")
    min_chunk_size: int = Field(default=20, ge=1,
                                description="Chunks shorter than this are discarded.")
    respect_word_boundaries: bool = Field(
        default=True,
        description="Avoid splitting in the middle of a word when possible.",
    )
    strip_whitespace: bool = Field(
        default=True,
        description="Strip leading/trailing whitespace from each chunk.",
    )

    model_config = {"extra": "ignore"}


class RetrievalConfig(BaseModel):
    """Configuration for RetrievalEngine."""

    limit: int = Field(default=5, ge=1, le=100,
                       description="Maximum results returned per query.")
    threshold: float = Field(default=0.0, ge=0.0, le=1.0,
                             description="Minimum cosine similarity to keep.")
    mmr_lambda: float = Field(
        default=0.7, ge=0.0, le=1.0,
        description=(
            "MMR diversity weight. 1.0 = pure relevance, "
            "0.0 = pure diversity. Values between 0.5–0.8 work well."
        ),
    )
    use_mmr: bool = Field(default=False,
                          description="Apply Maximal Marginal Relevance deduplication.")
    collections: List[str] = Field(
        default_factory=list,
        description="Collections to search. Empty = all domain collections.",
    )

    model_config = {"extra": "ignore"}


class StorageConfig(BaseModel):
    """Configuration for StorageEngine."""

    batch_size: int = Field(default=64, ge=1, le=512,
                            description="Maximum chunks per ChromaDB upsert call.")
    deduplicate: bool = Field(
        default=True,
        description="Skip storing a chunk whose content hash already exists in the collection.",
    )
    versioning_enabled: bool = Field(
        default=True,
        description="Mirror every ingestion into the project_history collection.",
    )

    model_config = {"extra": "ignore"}


class RAGConfig(BaseModel):
    """Top-level configuration that bundles all three sub-configs."""

    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)

    model_config = {"extra": "ignore"}


# ---------------------------------------------------------------------------
# Metadata filtering
# ---------------------------------------------------------------------------

class MetadataFilter(BaseModel):
    """
    Structured metadata filter for retrieval queries.

    Supports flat equality filters combinable with AND / OR logic.

    Example::

        MetadataFilter(
            operator=FilterOperator.AND,
            conditions={"agent_name": "backend_developer", "version": 2}
        )
    """
    conditions: Dict[str, Any] = Field(
        default_factory=dict,
        description="Key → value equality conditions.",
    )
    operator: FilterOperator = Field(
        default=FilterOperator.AND,
        description="Logical combination of all conditions.",
    )

    def to_chroma_where(self) -> Optional[Dict[str, Any]]:
        """
        Convert to a ChromaDB ``where`` clause.

        ChromaDB supports ``$and`` / ``$or`` list operators when combining
        multiple conditions.  A single-condition filter is returned as-is
        (no wrapping operator needed).

        Returns:
            A ChromaDB-compatible ``where`` dict, or ``None`` if there are
            no conditions.
        """
        if not self.conditions:
            return None

        clauses = [{k: {"$eq": v}} for k, v in self.conditions.items()]

        if len(clauses) == 1:
            # ChromaDB expects {field: {$eq: value}} for single conditions
            return clauses[0]

        op_key = "$and" if self.operator == FilterOperator.AND else "$or"
        return {op_key: clauses}


# ---------------------------------------------------------------------------
# Data records
# ---------------------------------------------------------------------------

class ChunkRecord(BaseModel):
    """
    Enriched chunk produced by the ChunkingEngine.

    Extends the basic ``TextChunk`` with all metadata needed for storage.
    """
    chunk_id: str             # UUID assigned at ingestion time
    chunk_index: int
    total_chunks: int
    content: str
    char_start: int
    char_end: int
    content_hash: str         # SHA-256 hex digest of the content
    source_artifact_type: str = ""
    strategy: ChunkStrategy = ChunkStrategy.CHARACTER
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RetrievalResult(BaseModel):
    """One result entry returned by the RetrievalEngine."""
    id: str
    document: str
    metadata: Dict[str, Any]
    similarity_score: float
    collection: str           # which collection this hit came from


class IngestionResult(BaseModel):
    """Summary returned after a StorageEngine.ingest() call."""
    project_id: int
    collection_name: str
    total_chunks: int
    stored_chunks: int        # chunks actually written (dedup may reduce this)
    skipped_chunks: int       # chunks skipped due to dedup
    first_id: str             # ID of the first stored chunk (or "")
    version: int
