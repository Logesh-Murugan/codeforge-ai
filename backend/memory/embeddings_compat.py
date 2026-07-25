"""
Backward-compatibility shim.

Old import path:  from memory.embeddings import BaseEmbeddings, LocalEmbeddings
New import path:  from memory.embeddings import LocalEmbeddings  (same package, new module)

This file is kept so that any external code still using the flat import
continues to work.  New code should import from the sub-packages directly.
"""
# Re-export new providers under both old and new names
from memory.embeddings.local import LocalEmbeddings
from memory.embeddings.ollama import OllamaEmbeddings
from memory.embeddings.huggingface import HuggingFaceEmbeddings
from memory.interfaces.embedding import EmbeddingProviderInterface as BaseEmbeddings

# OpenAI provider removed per project constraint (no vendor lock-in).
# Any code referencing OpenAIEmbeddings must be updated to use
# OllamaEmbeddings (local) or HuggingFaceEmbeddings (cloud).
__all__ = [
    "BaseEmbeddings",
    "LocalEmbeddings",
    "OllamaEmbeddings",
    "HuggingFaceEmbeddings",
]
