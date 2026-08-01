"""
EmbeddingManager — Phase 5.6

Manages embedding model enumeration, validation, metadata, and compatibility recommendations.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from ai_mode_manager.config.ai_config import ai_config
from ai_mode_manager.schemas.mode_state import WorkingMode
from ai_mode_manager.schemas.request_response import EmbeddingInfoResponse

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """
    Embedding Manager.
    """

    def list_available_embeddings(self, mode: Optional[WorkingMode] = None) -> List[EmbeddingInfoResponse]:
        """List all supported embedding models for the specified or active mode."""
        active_mode = mode or ai_config.CURRENT_MODE
        if active_mode == WorkingMode.LOCAL:
            embeddings = ai_config.LOCAL_EMBEDDINGS
            provider_name = "ollama"
        else:
            embeddings = ai_config.CLOUD_EMBEDDINGS
            provider_name = "sentence-transformers"

        return [
            EmbeddingInfoResponse(
                name=e,
                provider=provider_name,
                dimension=384,
            )
            for e in embeddings
        ]

    def get_current_embedding(self) -> str:
        """Return currently configured active embedding."""
        return ai_config.CURRENT_EMBEDDING

    def validate_embedding(self, embedding_name: str, mode: Optional[WorkingMode] = None) -> bool:
        """Check if embedding model is supported in mode."""
        active_mode = mode or ai_config.CURRENT_MODE
        allowed = (
            ai_config.LOCAL_EMBEDDINGS
            if active_mode == WorkingMode.LOCAL
            else ai_config.CLOUD_EMBEDDINGS
        )
        return embedding_name in allowed

    def recommend_compatible_embedding(self, embedding_name: str, mode: Optional[WorkingMode] = None) -> str:
        """Recommend supported fallback embedding if requested embedding is unavailable."""
        active_mode = mode or ai_config.CURRENT_MODE
        return "nomic-embed-text" if active_mode == WorkingMode.LOCAL else "all-MiniLM-L6-v2"
