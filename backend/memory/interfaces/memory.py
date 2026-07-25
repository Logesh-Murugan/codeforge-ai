"""
MemoryProviderInterface — top-level contract for the unified memory facade.

MemoryService implements this interface, allowing the orchestrator and
agents to depend only on the abstraction, not the concrete service.
"""
import abc
from typing import Any, Dict, List


class MemoryProviderInterface(abc.ABC):
    """Abstract contract for the memory service façade."""

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def store_memory(
        self,
        project_id: int,
        agent_name: str,
        artifact_type: str,
        collection_name: str,
        content: str,
        version: int = 1,
    ) -> str:
        """
        Embed and persist one text artifact.

        Args:
            project_id:      Owning project.
            agent_name:      Agent that produced the artifact.
            artifact_type:   Descriptor key (e.g. "db_schema", "api_contract").
            collection_name: Target collection group.
            content:         Text payload to store.
            version:         Iteration counter for the artifact.

        Returns:
            Generated memory UUID, or empty string on a silently skipped
            empty-content insertion.
        """

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def retrieve_memory(
        self,
        project_id: int,
        collection_name: str,
        query: str,
        limit: int = 5,
        threshold: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search scoped to a project.

        Args:
            project_id:      Scope filter.
            collection_name: Target collection.
            query:           Natural-language search text.
            limit:           Maximum results to return.
            threshold:       Minimum cosine similarity (0.0 – 1.0).

        Returns:
            List of result dicts, descending similarity order::

                [{"id": str, "document": str,
                  "metadata": dict, "similarity_score": float}, ...]
        """

    @abc.abstractmethod
    def get_project_memory(
        self, project_id: int, collection_name: str
    ) -> List[Dict[str, Any]]:
        """Return all raw entries for a project in a collection."""

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def delete_project_memory(self, project_id: int) -> None:
        """Wipe all memory entries for a project across all collections."""
