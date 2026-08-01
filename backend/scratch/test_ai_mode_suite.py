"""
Verification Suite — Phase 5.6 AI Mode Manager
"""
import asyncio
import sys

from ai_mode_manager.config.ai_config import ai_config
from ai_mode_manager.providers.ollama_provider import OllamaProvider
from ai_mode_manager.providers.groq_provider import GroqProvider
from ai_mode_manager.registry.provider_registry import provider_registry
from ai_mode_manager.services.mode_manager import mode_manager
from ai_mode_manager.llms.model_manager import ModelManager
from ai_mode_manager.embeddings.embedding_manager import EmbeddingManager
from ai_mode_manager.health.health_checker import ProviderHealthChecker
from ai_mode_manager.schemas.mode_state import WorkingMode, ProviderType, HealthStatus


async def run_all_tests():
    print("--- 1. Testing OllamaProvider & GroqProvider Metadata ---")
    ollama = OllamaProvider()
    assert ollama.get_metadata().provider_type == ProviderType.OLLAMA
    assert ollama.get_metadata().mode == WorkingMode.LOCAL
    assert "qwen2.5-coder" in ollama.list_supported_models()

    groq = GroqProvider()
    assert groq.get_metadata().provider_type == ProviderType.GROQ
    assert groq.get_metadata().mode == WorkingMode.CLOUD
    assert "llama-3.1-8b" in groq.list_supported_models()
    print("Provider tests PASSED ✅")

    print("\n--- 2. Testing ProviderRegistry O(1) Lookup ---")
    assert provider_registry.provider_exists("groq") is True
    assert provider_registry.provider_exists("ollama") is True
    assert isinstance(provider_registry.get_provider("groq"), GroqProvider)
    assert len(provider_registry.list_providers()) >= 2
    print("Registry tests PASSED ✅")

    print("\n--- 3. Testing ModeManager Switching ---")
    cfg_local = await mode_manager.switch_mode(WorkingMode.LOCAL)
    assert cfg_local.mode == WorkingMode.LOCAL
    assert mode_manager.get_current_mode() == WorkingMode.LOCAL

    cfg_cloud = await mode_manager.switch_mode(WorkingMode.CLOUD)
    assert cfg_cloud.mode == WorkingMode.CLOUD
    assert mode_manager.get_current_mode() == WorkingMode.CLOUD
    print("Mode switching tests PASSED ✅")

    print("\n--- 4. Testing ModelManager & EmbeddingManager ---")
    mm = ModelManager()
    em = EmbeddingManager()
    assert mm.validate_model("llama-3.1-8b", WorkingMode.CLOUD) is True
    assert em.validate_embedding("all-MiniLM-L6-v2", WorkingMode.CLOUD) is True
    print("Model & Embedding manager tests PASSED ✅")

    print("\n--- 5. Testing ProviderHealthChecker ---")
    checker = ProviderHealthChecker()
    status_map = await checker.check_all_providers_health()
    assert "Groq Cloud Provider" in status_map or "groq" in status_map or len(status_map) >= 2
    print("Health checker tests PASSED ✅")

    print("\n--- 6. Testing ModeManager Configuration & Status ---")
    status_dict = await mode_manager.get_provider_status()
    assert status_dict["provider"] == "Groq Cloud" or status_dict["provider"] == "groq"
    val = mode_manager.validate_configuration()
    assert val["is_valid"] is True
    print("Configuration & status tests PASSED ✅")

    print("\n==========================================")
    print("ALL PHASE 5.6 VERIFICATION TESTS PASSED SUCCESSFULLY! ✅")
    print("==========================================")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
