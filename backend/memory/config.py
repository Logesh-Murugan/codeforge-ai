"""
Memory subsystem configuration.

All tunables are read from environment variables with safe defaults.
Import the ``settings`` singleton — never instantiate MemorySettings
directly.

    from memory.config import settings
"""
from __future__ import annotations

import os
from typing import List

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings


class MemorySettings(BaseSettings):
    """
    Configuration for the memory subsystem.

    Priority: environment variable > .env file > default value.
    """

    # ------------------------------------------------------------------
    # Mode + provider selection
    # ------------------------------------------------------------------

    MEMORY_MODE: str = Field(
        default="local",
        description="Deployment mode: 'local' (Ollama) or 'cloud' (HuggingFace).",
    )

    EMBEDDING_PROVIDER: str = Field(
        default="local",
        description="Primary embedding provider: 'local', 'ollama', or 'huggingface'.",
    )

    EMBEDDING_FALLBACK_CHAIN: str = Field(
        default="ollama,huggingface,local",
        description="Comma-separated fallback provider order.",
    )

    # ------------------------------------------------------------------
    # Local (hash-projection) provider
    # ------------------------------------------------------------------

    LOCAL_EMBEDDING_DIMENSION: int = Field(
        default=1536,
        description="Vector dimension for the LocalEmbeddings provider.",
    )

    # ------------------------------------------------------------------
    # Ollama provider
    # ------------------------------------------------------------------

    OLLAMA_BASE_URL: str = Field(
        default="http://localhost:11434",
        description="Ollama server base URL.",
    )

    OLLAMA_EMBED_MODEL: str = Field(
        default="nomic-embed-text",
        description="Ollama embedding model to use.",
    )

    OLLAMA_TIMEOUT_SECONDS: int = Field(
        default=30,
        description="HTTP request timeout for Ollama API calls.",
    )

    # ------------------------------------------------------------------
    # HuggingFace provider
    # ------------------------------------------------------------------

    HF_API_TOKEN: str = Field(
        default="",
        description="HuggingFace API token (required for cloud mode).",
    )

    HF_EMBED_MODEL: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="HuggingFace Inference API model ID.",
    )

    HF_EMBED_TIMEOUT: int = Field(
        default=30,
        description="HTTP request timeout for HuggingFace API calls.",
    )

    # ------------------------------------------------------------------
    # ChromaDB
    # ------------------------------------------------------------------

    CHROMA_PERSIST_PATH: str = Field(
        default="",
        description=(
            "Directory for Chroma persistent storage. "
            "Defaults to <repo-root>/data/chroma_db."
        ),
    )

    # ------------------------------------------------------------------
    # RAG pipeline
    # ------------------------------------------------------------------

    RAG_CHUNK_SIZE: int = Field(
        default=800,
        description="Target character count per text chunk.",
    )

    RAG_CHUNK_OVERLAP: int = Field(
        default=100,
        description="Character overlap between consecutive chunks.",
    )

    RAG_DEFAULT_LIMIT: int = Field(
        default=5,
        description="Default number of results for similarity searches.",
    )

    RAG_DEFAULT_THRESHOLD: float = Field(
        default=0.0,
        description="Default minimum cosine similarity threshold.",
    )

    # ------------------------------------------------------------------
    # Embedding cache
    # ------------------------------------------------------------------

    EMBEDDING_CACHE_ENABLED: bool = Field(
        default=True,
        description="Enable in-process LRU cache for embeddings.",
    )

    EMBEDDING_CACHE_MAX_SIZE: int = Field(
        default=512,
        description="Maximum number of entries in the embedding LRU cache.",
    )

    # ------------------------------------------------------------------
    # Context injection
    # ------------------------------------------------------------------

    MAX_CONTEXT_CHUNKS: int = Field(
        default=5,
        description="Maximum memory chunks injected into each agent prompt.",
    )

    CONTEXT_SIMILARITY_THRESHOLD: float = Field(
        default=0.2,
        description="Minimum similarity score for context injection.",
    )

    CONVERSATION_WINDOW_SIZE: int = Field(
        default=10,
        description="Number of recent conversation turns retained per project.",
    )

    # ------------------------------------------------------------------
    # Computed / derived
    # ------------------------------------------------------------------

    @model_validator(mode="after")
    def _resolve_chroma_path(self) -> "MemorySettings":
        if not self.CHROMA_PERSIST_PATH:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.CHROMA_PERSIST_PATH = os.path.join(base, "data", "chroma_db")
        return self

    def get_fallback_chain(self) -> List[str]:
        """Return the parsed fallback chain list."""
        return [p.strip() for p in self.EMBEDDING_FALLBACK_CHAIN.split(",") if p.strip()]

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


# Singleton — import this throughout the memory subsystem
settings = MemorySettings()
