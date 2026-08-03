"""
ProviderRegistry — Phase 5.6

O(1) thread-safe registry for discovering and managing AI Providers.
Supports lazy provider instantiation and re-entrant thread safety.
"""
from __future__ import annotations

import logging
import threading
from typing import Callable, Dict, List, Optional, Type

from ai_mode_manager.providers.base_provider import AIProvider
from ai_mode_manager.providers.groq_provider import GroqProvider
from ai_mode_manager.providers.ollama_provider import OllamaProvider

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """
    Provider Registry System ($O(1)$ lookup with lazy initialization).
    """

    _instance: Optional[ProviderRegistry] = None
    _lock = threading.RLock()

    def __new__(cls) -> ProviderRegistry:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._providers: Dict[str, AIProvider] = {}
                cls._instance._factories: Dict[str, Callable[[], AIProvider]] = {}
                cls._instance._initialize_default_providers()
            return cls._instance

    def _initialize_default_providers(self) -> None:
        """Register built-in Ollama and Groq provider factories lazily."""
        self._register_factory_unlocked("ollama", OllamaProvider)
        self._register_factory_unlocked("groq", GroqProvider)

    def _register_factory_unlocked(self, provider_id: str, factory: Callable[[], AIProvider]) -> None:
        pid = provider_id.lower()
        self._factories[pid] = factory
        logger.info(f"[ProviderRegistry] Registered provider factory for '{provider_id}'")

    def register_provider(self, provider_id: str, provider: AIProvider) -> None:
        """
        Register a concrete provider instance ($O(1)$).
        """
        with self._lock:
            pid = provider_id.lower()
            self._providers[pid] = provider
            logger.info(f"[ProviderRegistry] Registered provider '{provider_id}'")

    def register_factory(self, provider_id: str, factory: Callable[[], AIProvider]) -> None:
        """
        Register a lazy provider factory ($O(1)$).
        """
        with self._lock:
            self._register_factory_unlocked(provider_id, factory)

    def remove_provider(self, provider_id: str) -> bool:
        """
        Remove a provider instance/factory ($O(1)$).
        """
        with self._lock:
            pid = provider_id.lower()
            removed = False
            if pid in self._providers:
                del self._providers[pid]
                removed = True
            if pid in self._factories:
                del self._factories[pid]
                removed = True
            if removed:
                logger.info(f"[ProviderRegistry] Removed provider '{provider_id}'")
            return removed

    def _ensure_instantiated_unlocked(self, pid: str) -> Optional[AIProvider]:
        if pid in self._providers:
            return self._providers[pid]
        if pid in self._factories:
            try:
                provider = self._factories[pid]()
                self._providers[pid] = provider
                return provider
            except Exception as exc:
                logger.error(f"[ProviderRegistry] Error instantiating provider '{pid}': {exc}")
                return None
        return None

    def get_provider(self, provider_id: str) -> Optional[AIProvider]:
        """
        Retrieve provider instance by ID ($O(1)$), instantiating lazily if needed.
        """
        with self._lock:
            return self._ensure_instantiated_unlocked(provider_id.lower())

    def list_providers(self) -> List[AIProvider]:
        """
        List all registered provider instances, instantiating any registered factories.
        """
        with self._lock:
            all_ids = set(self._providers.keys()) | set(self._factories.keys())
            providers: List[AIProvider] = []
            for pid in sorted(all_ids):
                p = self._ensure_instantiated_unlocked(pid)
                if p is not None:
                    providers.append(p)
            return providers

    def provider_exists(self, provider_id: str) -> bool:
        """
        Check if provider or provider factory is registered ($O(1)$).
        """
        with self._lock:
            pid = provider_id.lower()
            return pid in self._providers or pid in self._factories


def get_provider_registry() -> ProviderRegistry:
    """Dependency injection helper / lazy accessor for ProviderRegistry."""
    return ProviderRegistry()


provider_registry = ProviderRegistry()

