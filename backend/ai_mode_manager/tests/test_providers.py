"""
Provider Tests — Phase 5.6
"""
import pytest
from ai_mode_manager.providers.groq_provider import GroqProvider
from ai_mode_manager.providers.ollama_provider import OllamaProvider
from ai_mode_manager.schemas.mode_state import ProviderType, WorkingMode


def test_ollama_provider_metadata():
    provider = OllamaProvider()
    meta = provider.get_metadata()
    assert meta.provider_type == ProviderType.OLLAMA
    assert meta.mode == WorkingMode.LOCAL
    assert "qwen2.5-coder" in provider.list_supported_models()


def test_groq_provider_metadata():
    provider = GroqProvider()
    meta = provider.get_metadata()
    assert meta.provider_type == ProviderType.GROQ
    assert meta.mode == WorkingMode.CLOUD
    assert "llama-3.1-8b" in provider.list_supported_models()
