"""
ProviderFactory — Phase 5.6

Factory pattern implementation for instantiating AI providers.
"""
from __future__ import annotations

import logging
from typing import Dict, Type

from ai_mode_manager.providers.base_provider import AIProvider
from ai_mode_manager.providers.groq_provider import GroqProvider
from ai_mode_manager.providers.ollama_provider import OllamaProvider

logger = logging.getLogger(__name__)


class ProviderFactory:
    """
    Provider Factory.
    """

    _PROVIDERS: Dict[str, Type[AIProvider]] = {
        "ollama": OllamaProvider,
        "groq": GroqProvider,
    }

    @classmethod
    def create_provider(cls, provider_id: str, **kwargs) -> AIProvider:
        """
        Instantiate and return an AIProvider subclass.
        """
        provider_class = cls._PROVIDERS.get(provider_id.lower())
        if not provider_class:
            logger.warning(f"[ProviderFactory] Unknown provider '{provider_id}', falling back to GroqProvider.")
            return GroqProvider(**kwargs)
        return provider_class(**kwargs)

    @classmethod
    def register_factory_provider(cls, provider_id: str, provider_class: Type[AIProvider]) -> None:
        """Register a new provider class into the factory dynamically."""
        cls._PROVIDERS[provider_id.lower()] = provider_class
