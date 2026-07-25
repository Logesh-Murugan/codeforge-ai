"""
Embedding providers package.

Public API
----------
from memory.embeddings import LocalEmbeddings
from memory.embeddings import OllamaEmbeddings
from memory.embeddings import HuggingFaceEmbeddings
from memory.embeddings import resolve_provider
"""
from memory.embeddings.local import LocalEmbeddings
from memory.embeddings.ollama import OllamaEmbeddings
from memory.embeddings.huggingface import HuggingFaceEmbeddings
from memory.embeddings.resolver import resolve_provider

__all__ = [
    "LocalEmbeddings",
    "OllamaEmbeddings",
    "HuggingFaceEmbeddings",
    "resolve_provider",
]
