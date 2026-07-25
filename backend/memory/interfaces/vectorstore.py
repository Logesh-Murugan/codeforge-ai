"""
VectorStoreInterface — contract all vector-storage backends must satisfy.

Currently implemented by ChromaStoreManager (ChromaDB backend).
Future backends (Qdrant, pgvector, FAISS) can be swapped in by
implementing this contract and updating MemoryConfig.VECTOR_STORE_BACKEND.
"""
import abc
from typing import Any, Dict, List, Optional


class VectorStoreInterface(abc.ABC):
    """Abstract base class for any vector storage backend."""

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def store(
        self,
        collection_name: str,
        ids: List[str],
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        """
        Upsert documents with their pre-computed embeddings.

        All four lists must have the same length.  If a document with
        the same ``id`` already exists it is overwritten (upsert).

        Args:
            collection_name: Logical collection / namespace.
            ids:             Stable unique IDs for each document.
            documents:       Raw text payloads.
            embeddings:      Pre-computed embedding vectors.
            metadatas:       Flat dict metadata for each document.
        """

    @abc.abstractmethod
    def delete_by_project(self, collection_name: str, project_id: int) -> None:
        """
        Hard-delete every document whose metadata ``project_id`` matches.

        Args:
            collection_name: Target collection.
            project_id:      Project scope to wipe.
        """

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def query(
        self,
        collection_name: str,
        query_embeddings: List[List[float]],
        project_id: int,
        limit: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Approximate-nearest-neighbour search scoped to a project.

        Args:
            collection_name:   Target collection.
            query_embeddings:  List containing one query vector.
            project_id:        Filter results to this project.
            limit:             Maximum number of results.
            where:             Optional pre-built ChromaDB ``where`` clause
                               (overrides the default project_id filter when
                               supplied — caller is responsible for including
                               project_id in the clause).

        Returns:
            Raw backend results dict with at least the keys:
            ``ids``, ``documents``, ``metadatas``.
        """

    @abc.abstractmethod
    def get_all(self, collection_name: str, project_id: int) -> Dict[str, Any]:
        """
        Return every document in *collection_name* for *project_id*.

        Returns:
            Dict with ``ids``, ``documents``, ``metadatas``.
        """

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def get_collection_size(self, collection_name: str) -> int:
        """Total document count in *collection_name* (across all projects)."""

    @abc.abstractmethod
    def get_collection(self, collection_name: str) -> Any:
        """
        Return the raw backend collection object.

        This is intentionally backend-specific (e.g. a
        ``chromadb.Collection`` instance).  Callers that use this method
        must be aware of the concrete backend in use.
        """
