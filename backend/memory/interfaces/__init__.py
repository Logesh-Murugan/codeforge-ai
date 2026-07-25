"""
Memory subsystem interface contracts.

Import from here to avoid deep path coupling:

    from memory.interfaces import EmbeddingProviderInterface
    from memory.interfaces import VectorStoreInterface
    from memory.interfaces import MemoryProviderInterface
"""
from memory.interfaces.embedding import EmbeddingProviderInterface
from memory.interfaces.vectorstore import VectorStoreInterface
from memory.interfaces.memory import MemoryProviderInterface

__all__ = [
    "EmbeddingProviderInterface",
    "VectorStoreInterface",
    "MemoryProviderInterface",
]
