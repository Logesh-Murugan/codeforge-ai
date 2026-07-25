"""
Backward-compatibility shim.

Old import path:  from memory.vector_store import ChromaStoreManager
New import path:  from memory.vectorstores import ChromaVectorStore

ChromaStoreManager is now an alias for ChromaVectorStore.
The COLLECTION_TYPES list is preserved on the class for callers that
reference it directly.
"""
from memory.vectorstores.chroma import ChromaVectorStore

# Alias under old name so existing imports keep working
ChromaStoreManager = ChromaVectorStore

__all__ = ["ChromaStoreManager", "ChromaVectorStore"]
