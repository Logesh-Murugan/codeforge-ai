"""
Registry Tests — Phase 5.6
"""
import pytest
from ai_mode_manager.registry.provider_registry import provider_registry
from ai_mode_manager.providers.groq_provider import GroqProvider


def test_provider_registry_lookup():
    assert provider_registry.provider_exists("groq") is True
    assert provider_registry.provider_exists("ollama") is True
    provider = provider_registry.get_provider("groq")
    assert isinstance(provider, GroqProvider)


def test_provider_registry_list():
    providers = provider_registry.list_providers()
    assert len(providers) >= 2
