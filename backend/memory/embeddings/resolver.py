"""
Embedding provider resolver — configuration-driven provider selection
with automatic fallback chain.

Usage
-----
    from memory.embeddings.resolver import resolve_provider

    provider = resolve_provider()   # reads env-vars automatically
"""
import logging
import os
from typing import List, Optional

from memory.interfaces.embedding import EmbeddingProviderInterface

logger = logging.getLogger(__name__)


def _try_build_ollama() -> Optional[EmbeddingProviderInterface]:
    """Attempt to construct and health-check an OllamaEmbeddings instance."""
    from memory.embeddings.ollama import OllamaEmbeddings  # local import

    try:
        provider = OllamaEmbeddings(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            model=os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
            timeout=int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "30")),
        )
        if provider.health_check():
            logger.info("[RESOLVER] Ollama health check passed — using OllamaEmbeddings")
            return provider
        logger.debug("[RESOLVER] Ollama health check failed — skipping")
    except Exception as exc:
        logger.debug("[RESOLVER] OllamaEmbeddings construction failed: %s", exc)
    return None


def _try_build_huggingface() -> Optional[EmbeddingProviderInterface]:
    """Attempt to construct and health-check a HuggingFaceEmbeddings instance."""
    from memory.embeddings.huggingface import HuggingFaceEmbeddings  # local import

    api_token = os.getenv("HF_API_TOKEN", "")
    if not api_token:
        logger.debug("[RESOLVER] HF_API_TOKEN not set — skipping HuggingFace provider")
        return None
    try:
        provider = HuggingFaceEmbeddings(
            api_token=api_token,
            model=os.getenv("HF_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
            timeout=int(os.getenv("HF_EMBED_TIMEOUT", "30")),
        )
        if provider.health_check():
            logger.info("[RESOLVER] HuggingFace health check passed — using HuggingFaceEmbeddings")
            return provider
        logger.debug("[RESOLVER] HuggingFace health check failed — skipping")
    except Exception as exc:
        logger.debug("[RESOLVER] HuggingFaceEmbeddings construction failed: %s", exc)
    return None


def _build_local() -> EmbeddingProviderInterface:
    """Always succeeds — returns the LocalEmbeddings fallback."""
    from memory.embeddings.local import LocalEmbeddings  # local import

    dim = int(os.getenv("LOCAL_EMBEDDING_DIMENSION", "1536"))
    provider = LocalEmbeddings(dim=dim)
    logger.info(
        "[RESOLVER] Using LocalEmbeddings (dim=%d) — zero-dependency fallback",
        dim,
    )
    return provider


_BUILDERS = {
    "ollama": _try_build_ollama,
    "huggingface": _try_build_huggingface,
    "local": None,  # sentinel — always succeeds
}


def resolve_provider(
    preferred: Optional[str] = None,
    fallback_chain: Optional[List[str]] = None,
) -> EmbeddingProviderInterface:
    """
    Return a live, healthy embedding provider.

    Resolution order
    ----------------
    1. ``preferred`` (if given and healthy).
    2. Each entry in ``fallback_chain`` in order.
    3. ``LocalEmbeddings`` unconditional final fallback.

    Args:
        preferred:      Override provider name: "ollama", "huggingface",
                        or "local".  When ``None`` the ``EMBEDDING_PROVIDER``
                        env-var is used (default: "local").
        fallback_chain: Override fallback order.  When ``None`` the
                        ``EMBEDDING_FALLBACK_CHAIN`` env-var is parsed
                        (default: ["ollama", "huggingface", "local"]).

    Returns:
        A healthy ``EmbeddingProviderInterface`` instance.
    """
    if preferred is None:
        preferred = os.getenv("EMBEDDING_PROVIDER", "local").lower()

    if fallback_chain is None:
        raw = os.getenv("EMBEDDING_FALLBACK_CHAIN", "ollama,huggingface,local")
        fallback_chain = [p.strip() for p in raw.split(",") if p.strip()]

    # Build ordered probe list: preferred first, then fallback chain (deduped)
    seen: set[str] = set()
    probe_order: List[str] = []
    for name in [preferred] + fallback_chain:
        if name not in seen:
            probe_order.append(name)
            seen.add(name)

    for name in probe_order:
        if name == "local":
            return _build_local()
        builder = _BUILDERS.get(name)
        if builder is None:
            logger.warning("[RESOLVER] Unknown provider '%s' — skipping", name)
            continue
        provider = builder()
        if provider is not None:
            return provider

    # Guaranteed fallback
    return _build_local()
