"""
ModeManager — Phase 5.6

Core ModeManager exposing required public API methods:
- switch_mode()
- get_current_mode()
- get_current_provider()
- get_current_model()
- get_current_embedding()
- get_provider_status()
- get_configuration()
- update_configuration()
- validate_configuration()
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ai_mode_manager.config.ai_config import ai_config
from ai_mode_manager.embeddings.embedding_manager import EmbeddingManager
from ai_mode_manager.health.health_checker import ProviderHealthChecker
from ai_mode_manager.llms.model_manager import ModelManager
from ai_mode_manager.registry.provider_registry import provider_registry
from ai_mode_manager.schemas import (
    AIConfigResponse,
    HealthStatus,
    ModeState,
    SwitchModeRequest,
    UpdateConfigRequest,
    WorkingMode,
)

logger = logging.getLogger(__name__)


class ModeManager:
    """
    Unified AI Mode Manager Gateway for CodeForge AI.
    """

    def __init__(
        self,
        health_checker: Optional[ProviderHealthChecker] = None,
        model_manager: Optional[ModelManager] = None,
        embedding_manager: Optional[EmbeddingManager] = None,
    ) -> None:
        self._health_checker = health_checker
        self._model_manager = model_manager
        self._embedding_manager = embedding_manager

    @property
    def health_checker(self) -> ProviderHealthChecker:
        if self._health_checker is None:
            self._health_checker = ProviderHealthChecker()
        return self._health_checker

    @property
    def model_manager(self) -> ModelManager:
        if self._model_manager is None:
            self._model_manager = ModelManager()
        return self._model_manager

    @property
    def embedding_manager(self) -> EmbeddingManager:
        if self._embedding_manager is None:
            self._embedding_manager = EmbeddingManager()
        return self._embedding_manager

    async def switch_mode(
        self,
        mode: WorkingMode,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        embedding: Optional[str] = None,
    ) -> AIConfigResponse:
        """
        Switch system execution mode between LOCAL and CLOUD.
        """
        logger.info(f"[ModeManager] Switching mode to '{mode.value}'")

        ai_config.CURRENT_MODE = mode

        # Set provider defaults per mode
        if mode == WorkingMode.LOCAL:
            ai_config.CURRENT_PROVIDER = provider or "ollama"
            ai_config.CURRENT_MODEL = model or "qwen2.5-coder"
            ai_config.CURRENT_EMBEDDING = embedding or "nomic-embed-text"
        else:
            ai_config.CURRENT_PROVIDER = provider or "groq"
            ai_config.CURRENT_MODEL = model or "llama-3.1-8b"
            ai_config.CURRENT_EMBEDDING = embedding or "all-MiniLM-L6-v2"

        health = await self.health_checker.get_active_mode_health()
        ai_config.HEALTH_STATUS = health

        return self.get_configuration()

    def get_current_mode(self) -> WorkingMode:
        """Return active WorkingMode (local or cloud)."""
        return ai_config.CURRENT_MODE

    def get_current_provider(self) -> str:
        """Return active provider name."""
        return ai_config.CURRENT_PROVIDER

    def get_current_model(self) -> str:
        """Return active LLM model."""
        return ai_config.CURRENT_MODEL

    def get_current_embedding(self) -> str:
        """Return active embedding model."""
        return ai_config.CURRENT_EMBEDDING

    async def get_provider_status(self) -> Dict[str, Any]:
        """Get detailed status of active provider and capabilities."""
        provider = provider_registry.get_provider(ai_config.CURRENT_PROVIDER)
        if not provider:
            return {
                "provider": ai_config.CURRENT_PROVIDER,
                "status": HealthStatus.UNAVAILABLE.value,
                "mode": ai_config.CURRENT_MODE.value,
            }

        health = await provider.check_health()
        info = provider.get_information()
        return {
            "provider": provider.name,
            "status": health.value,
            "mode": provider.mode.value,
            "information": info.model_dump(),
        }

    def get_configuration(self) -> AIConfigResponse:
        """Retrieve current AIConfiguration snapshot."""
        return AIConfigResponse(
            mode=ai_config.CURRENT_MODE,
            active_provider=ai_config.CURRENT_PROVIDER,
            active_model=ai_config.CURRENT_MODEL,
            active_embedding=ai_config.CURRENT_EMBEDDING,
            health_status=ai_config.HEALTH_STATUS,
            validation_status="valid",
            available_modes=["local", "cloud"],
        )

    async def update_configuration(self, req: UpdateConfigRequest) -> AIConfigResponse:
        """Update provider, model, embedding or settings."""
        if req.mode is not None:
            ai_config.CURRENT_MODE = req.mode
        if req.provider is not None:
            ai_config.CURRENT_PROVIDER = req.provider
        if req.model is not None:
            ai_config.CURRENT_MODEL = req.model
        if req.embedding is not None:
            ai_config.CURRENT_EMBEDDING = req.embedding

        health = await self.health_checker.get_active_mode_health()
        ai_config.HEALTH_STATUS = health

        return self.get_configuration()

    def validate_configuration(self) -> Dict[str, Any]:
        """Validate current configuration integrity."""
        valid_model = self.model_manager.validate_model(
            ai_config.CURRENT_MODEL, ai_config.CURRENT_MODE
        )
        valid_emb = self.embedding_manager.validate_embedding(
            ai_config.CURRENT_EMBEDDING, ai_config.CURRENT_MODE
        )
        valid_provider = provider_registry.provider_exists(ai_config.CURRENT_PROVIDER)

        is_valid = valid_model and valid_emb and valid_provider

        recommendations = {}
        if not valid_model:
            recommendations["model"] = self.model_manager.recommend_alternative_model(
                ai_config.CURRENT_MODEL, ai_config.CURRENT_MODE
            )
        if not valid_emb:
            recommendations["embedding"] = self.embedding_manager.recommend_compatible_embedding(
                ai_config.CURRENT_EMBEDDING, ai_config.CURRENT_MODE
            )

        return {
            "is_valid": is_valid,
            "valid_provider": valid_provider,
            "valid_model": valid_model,
            "valid_embedding": valid_emb,
            "recommendations": recommendations,
        }


_mode_manager_instance: Optional[ModeManager] = None


def get_mode_manager() -> ModeManager:
    """Dependency injection helper / lazy accessor for ModeManager."""
    global _mode_manager_instance
    if _mode_manager_instance is None:
        _mode_manager_instance = ModeManager()
    return _mode_manager_instance


class _LazyModeManagerProxy:
    """Proxy object for backward compatibility with `mode_manager` imports."""

    def __getattr__(self, name: str) -> Any:
        return getattr(get_mode_manager(), name)


mode_manager = _LazyModeManagerProxy()

