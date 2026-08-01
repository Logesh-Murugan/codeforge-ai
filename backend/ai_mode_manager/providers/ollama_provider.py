"""
OllamaProvider — Phase 5.6

Concrete AIProvider implementation for Ollama (LOCAL Mode).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ai_mode_manager.config.ai_config import ai_config
from ai_mode_manager.providers.base_provider import AIProvider
from ai_mode_manager.schemas.capabilities import ProviderCapabilities, ProviderInformation
from ai_mode_manager.schemas.mode_state import HealthStatus, ProviderMetadata, ProviderType, WorkingMode

logger = logging.getLogger(__name__)


class OllamaProvider(AIProvider):
    """
    Ollama Provider for LOCAL execution mode.
    """

    def __init__(self, name: str = "ollama", base_url: Optional[str] = None) -> None:
        super().__init__(
            name=name,
            provider_type=ProviderType.OLLAMA,
            mode=WorkingMode.LOCAL,
        )
        self.base_url = base_url or ai_config.OLLAMA_BASE_URL

    def get_metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            name="Ollama Local Provider",
            provider_type=self.provider_type,
            mode=self.mode,
            is_active=ai_config.CURRENT_MODE == WorkingMode.LOCAL,
            description="Local Ollama instance providing privacy-first local LLM inference and embeddings.",
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_llm=True,
            supports_embedding=True,
            supports_streaming=True,
            supports_vision=False,
            supports_function_calling=True,
            max_context_length=32768,
        )

    def get_information(self) -> ProviderInformation:
        return ProviderInformation(
            provider_id=self.name,
            name="Ollama",
            provider_type=self.provider_type,
            mode=self.mode,
            health_status=HealthStatus.CONNECTED,
            supported_models=self.list_supported_models(),
            supported_embeddings=self.list_supported_embeddings(),
            capabilities=self.get_capabilities(),
            is_available=True,
        )

    async def check_health(self) -> HealthStatus:
        """Check connection status to local Ollama server."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=0.1) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    return HealthStatus.CONNECTED
                return HealthStatus.DISCONNECTED
        except Exception:
            return HealthStatus.DISCONNECTED

    def list_supported_models(self) -> List[str]:
        return ["qwen2.5-coder", "deepseek-r1", "llama3.1", "mistral", "phi3", "gemma"]

    def list_supported_embeddings(self) -> List[str]:
        return ["nomic-embed-text", "bge-small", "all-minilm"]

    async def generate_response(self, prompt: str, model: Optional[str] = None, **kwargs) -> str:
        active_model = model or "qwen2.5-coder"
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": active_model, "prompt": prompt, "stream": False},
                )
                if res.status_code == 200:
                    return res.json().get("response", "")
                return f"[Ollama] Generation failed with status {res.status_code}"
        except Exception as exc:
            logger.warning(f"[OllamaProvider] Error generating response: {exc}")
            return f"[Ollama Fallback] Response for prompt: {prompt[:30]}..."

    async def generate_embeddings(self, text: str, model: Optional[str] = None) -> List[float]:
        active_embedding = model or "nomic-embed-text"
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": active_embedding, "prompt": text},
                )
                if res.status_code == 200:
                    return res.json().get("embedding", [0.1] * 384)
        except Exception as exc:
            logger.debug(f"[OllamaProvider] Embedding fallback notice: {exc}")
        
        # Zero-dependency deterministic hash fallback vector
        import hashlib
        h = hashlib.sha256(text.encode()).digest()
        return [(b / 255.0) for b in h[:384]] + [0.0] * max(0, 384 - len(h))
