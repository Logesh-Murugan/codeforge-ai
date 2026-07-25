"""
Formal interface contracts for the memory subsystem.

All embedding providers and vector store backends must implement
these ABCs. This enables dependency inversion and easy substitution
(Ollama ↔ HuggingFace ↔ OpenAI; ChromaDB ↔ future backends).
"""
import abc
from typing import List, Dict, Any, Optional


class EmbeddingProviderInterface(abc.ABC):
    """
    Abstract contract for any embedding generation backend.

    Implementations: OllamaEmbeddings, HuggingFaceEmbeddings,
    OpenAIEmbeddings, LocalEmbeddings.
    """

    @abc.abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of documents.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of float vectors, one per input text.
        """

    @abc.abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """
        Generate an embedding optimised for similarity search queries.

        Args:
            text: Query string.

        Returns:
            Float vector representing the query.
        """

    @property
    @abc.abstractmethod
    def dimension(self) -> int:
        """Return the embedding vector dimensionality."""

    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        """Return a human-readable provider identifier."""

    def health_check(self) -> bool:
        """
        Optional liveness probe.  Providers that require a live service
        should override this and verify connectivity.

        Returns:
            True if the provider is available; False otherwise.
        """
        return True


class VectorStoreInterface(abc.ABC):
    """
    Abstract contract for any vector storage backend.

    Implementations: ChromaStoreManager (and future alternatives).
    """

    @abc.abstractmethod
    def store(
        self,
        collection_name: str,
        ids: List[str],
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        """Upsert documents with pre-computed embeddings into a collection."""

    @abc.abstractmethod
    def query(
        self,
        collection_name: str,
        query_embeddings: List[List[float]],
        project_id: int,
        limit: int = 5,
    ) -> Dict[str, Any]:
        """Perform ANN search filtered to a project, returning raw backend results."""

    @abc.abstractmethod
    def get_all(self, collection_name: str, project_id: int) -> Dict[str, Any]:
        """Return every document in a collection belonging to a project."""

    @abc.abstractmethod
    def delete_by_project(self, collection_name: str, project_id: int) -> None:
        """Hard-delete all documents belonging to a project from a collection."""

    @abc.abstractmethod
    def get_collection_size(self, collection_name: str) -> int:
        """Return the total document count in a collection."""

    @abc.abstractmethod
    def get_collection(self, collection_name: str) -> Any:
        """Return the raw backend collection object (provider-specific)."""
