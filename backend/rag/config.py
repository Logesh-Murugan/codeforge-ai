"""
RAG Engine Configuration — Phase 5.2

Extends memory.config.settings with RAG-specific tunables.
All values are read from environment variables with safe defaults.

    from rag.config import rag_settings
"""
from __future__ import annotations

import os
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class RAGSettings(BaseSettings):
    """
    Configuration for the Phase 5.2 RAG Engine.

    All settings inherit from environment variables or .env file.
    Delegates embedding / ChromaDB configuration to memory.config.settings.
    """

    # ── Chunking ────────────────────────────────────────────────────────
    RAG_CHUNK_SIZE: int = Field(
        default=800,
        description="Maximum character count per text chunk during ingestion.",
    )

    RAG_CHUNK_OVERLAP: int = Field(
        default=100,
        description="Character overlap between consecutive chunks.",
    )

    # ── Retrieval defaults ───────────────────────────────────────────────
    RAG_DEFAULT_LIMIT: int = Field(
        default=5,
        description="Default maximum number of results returned by search.",
    )

    RAG_DEFAULT_THRESHOLD: float = Field(
        default=0.0,
        description="Default minimum cosine similarity threshold (0.0 = no filter).",
    )

    RAG_MAX_LIMIT: int = Field(
        default=100,
        description="Hard upper bound on search result limit (API validation).",
    )

    # ── Context assembly ─────────────────────────────────────────────────
    RAG_CONTEXT_MAX_CHUNKS: int = Field(
        default=8,
        description="Maximum number of chunks assembled into an agent context block.",
    )

    RAG_CONTEXT_THRESHOLD: float = Field(
        default=0.2,
        description="Minimum similarity for chunks included in context.",
    )

    RAG_CONTEXT_MAX_CHARS: int = Field(
        default=6000,
        description="Maximum total characters in a generated context block.",
    )

    # ── Batch ingestion ──────────────────────────────────────────────────
    RAG_BATCH_MAX_DOCUMENTS: int = Field(
        default=50,
        description="Maximum number of documents per batch ingestion request.",
    )

    # ── Available collections ────────────────────────────────────────────
    RAG_COLLECTIONS: str = Field(
        default=(
            "requirements,architecture,database_design,api_contracts,"
            "backend_code,frontend_code,security_reports,qa_reports,"
            "documentation,devops,conversation,project_history"
        ),
        description="Comma-separated list of valid collection names.",
    )

    def get_collections(self) -> List[str]:
        """Return the parsed list of available collection names."""
        return [c.strip() for c in self.RAG_COLLECTIONS.split(",") if c.strip()]

    def get_search_collections(self) -> List[str]:
        """Return collections appropriate for semantic search (exclude meta-collections)."""
        excluded = {"conversation", "project_history"}
        return [c for c in self.get_collections() if c not in excluded]

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


# Module-level singleton
rag_settings = RAGSettings()
