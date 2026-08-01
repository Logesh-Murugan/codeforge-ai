"""
AIProvider Base Class — Phase 5.6

Abstract Base Class (ABC) for all AI providers in CodeForge AI.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ai_mode_manager.schemas.capabilities import ProviderCapabilities, ProviderInformation
from ai_mode_manager.schemas.mode_state import HealthStatus, ProviderMetadata, ProviderType, WorkingMode


class AIProvider(ABC):
    """
    Abstract AI Provider contract interface.
    """

    def __init__(self, name: str, provider_type: ProviderType, mode: WorkingMode) -> None:
        self.name = name
        self.provider_type = provider_type
        self.mode = mode

    @abstractmethod
    def get_metadata(self) -> ProviderMetadata:
        """Get provider metadata details."""
        pass

    @abstractmethod
    def get_capabilities(self) -> ProviderCapabilities:
        """Get provider capabilities object."""
        pass

    @abstractmethod
    def get_information(self) -> ProviderInformation:
        """Get comprehensive provider information."""
        pass

    @abstractmethod
    async def check_health(self) -> HealthStatus:
        """Perform health check on provider reachability and status."""
        pass

    @abstractmethod
    def list_supported_models(self) -> List[str]:
        """List all supported LLM models for this provider."""
        pass

    @abstractmethod
    def list_supported_embeddings(self) -> List[str]:
        """List all supported embedding models for this provider."""
        pass

    @abstractmethod
    async def generate_response(self, prompt: str, model: Optional[str] = None, **kwargs) -> str:
        """Generate text response using this provider."""
        pass

    @abstractmethod
    async def generate_embeddings(self, text: str, model: Optional[str] = None) -> List[float]:
        """Generate text embedding vector using this provider."""
        pass
