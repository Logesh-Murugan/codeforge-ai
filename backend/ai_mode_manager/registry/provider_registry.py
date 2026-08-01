"""
ProviderRegistry — Phase 5.6

O(1) thread-safe registry for discovering and managing AI Providers.
"""
from __future__ import annotations

import logging
import threading
from typing import Dict, List, Optional

from ai_mode_manager.providers.base_provider import AIProvider
from ai_mode_manager.providers.groq_provider import GroqProvider
from ai_mode_manager.providers.ollama_provider import OllamaProvider

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """
    Provider Registry System ($O(1)$ lookup).
    """

    _instance: Optional[ProviderRegistry] = None
    _lock = threading.Lock()

    def __new__(cls) -> ProviderRegistry:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._providers = {}
                cls._instance._initialize_default_providers()
            return cls._instance

    def _initialize_default_providers(self) -> None:
        """Register built-in Ollama and Groq providers."""
        self.register_provider("ollama", OllamaProvider())
        self.register_provider("groq", GroqProvider())

    def register_provider(self, provider_id: str, provider: AIProvider) -> None:
        """
        Register a provider instance ($O(1)$).
        """
        with self._lock:
            self._providers[provider_id.lower()] = provider
            logger.info(f"[ProviderRegistry] Registered provider '{provider_id}'")

    def remove_provider(self, provider_id: str) -> bool:
        """
        Remove a provider instance ($O(1)$).
        """
        with self._lock:
            pid = provider_id.lower()
            if pid in self._providers:
                del self._providers[pid]
                logger.info(f"[ProviderRegistry] Removed provider '{provider_id}'")
                return True
            return False

    def get_provider(self, provider_id: str) -> Optional[AIProvider]:
        """
        Retrieve provider instance by ID ($O(1)$).
        """
        return self._providers.get(provider_id.lower())

    def list_providers(self) -> List[AIProvider]:
        """
        List all registered provider instances.
        """
        return list(self._providers.values())

    def provider_exists(self, provider_id: str) -> bool:
        """
        Check if provider is registered ($O(1)$).
        """
        return provider_id.lower() in self._providers


provider_registry = ProviderRegistry()
