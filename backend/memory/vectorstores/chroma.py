"""
ChromaVectorStore — ChromaDB implementation of VectorStoreInterface.

Manages all persistent Chroma collections used by the memory system.
The 10 collection types map directly to the pipeline's artifact
categories (requirements, architecture, backend_code, …).

All metadata keys stored alongside documents are flat scalar types
(str / int / float / bool) as required by ChromaDB.
"""
import logging
import os
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from memory.interfaces.vectorstore import VectorStoreInterface

logger = logging.getLogger(__name__)


class ChromaVectorStore(VectorStoreInterface):
    """
    Persistent ChromaDB vector store.

    Args:
        persist_path: Directory where Chroma stores its data on disk.
                      Created if it does not exist.
    """

    # Canonical collection names.  Agents write to a specific collection;
    # retrieval and deletion are always scoped to a project_id.
    COLLECTION_TYPES: List[str] = [
        "requirements",
        "architecture",
        "database_design",
        "api_contracts",
        "backend_code",
        "frontend_code",
        "security_reports",
        "qa_reports",
        "documentation",
        "devops",
        "conversation",   # Phase 3.5 — conversation memory
        "project_history", # Phase 3.4 — version-tracked history
    ]

    def __init__(self, persist_path: Optional[str] = None) -> None:
        if persist_path is None:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            persist_path = os.path.join(base, "data", "chroma_db")

        os.makedirs(persist_path, exist_ok=True)
        logger.info("[CHROMA] Initialising persistent client at: %s", persist_path)

        self._client = chromadb.PersistentClient(
            path=persist_path,
            settings=ChromaSettings(allow_reset=True),
        )

        # Eager collection initialisation so the first write is fast
        self._collections: Dict[str, chromadb.Collection] = {}
        for name in self.COLLECTION_TYPES:
            self._collections[name] = self._client.get_or_create_collection(name=name)

        logger.info(
            "[CHROMA] Registered %d collections: %s",
            len(self._collections),
            ", ".join(self.COLLECTION_TYPES),
        )

    # ------------------------------------------------------------------
    # VectorStoreInterface — write
    # ------------------------------------------------------------------

    def store(
        self,
        collection_name: str,
        ids: List[str],
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        col = self._resolve(collection_name)
        col.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        logger.debug(
            "[CHROMA] Upserted %d document(s) into '%s'",
            len(ids),
            collection_name,
        )

    def delete_by_project(self, collection_name: str, project_id: int) -> None:
        col = self._resolve(collection_name)
        col.delete(where={"project_id": project_id})
        logger.debug(
            "[CHROMA] Deleted entries for project_id=%d from '%s'",
            project_id,
            collection_name,
        )

    # ------------------------------------------------------------------
    # VectorStoreInterface — read
    # ------------------------------------------------------------------

    def query(
        self,
        collection_name: str,
        query_embeddings: List[List[float]],
        project_id: int,
        limit: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        col = self._resolve(collection_name)
        effective_where = where if where is not None else {"project_id": project_id}
        return col.query(
            query_embeddings=query_embeddings,
            n_results=limit,
            where=effective_where,
        )

    def get_all(self, collection_name: str, project_id: int) -> Dict[str, Any]:
        col = self._resolve(collection_name)
        return col.get(where={"project_id": project_id})

    # ------------------------------------------------------------------
    # VectorStoreInterface — utility
    # ------------------------------------------------------------------

    def get_collection_size(self, collection_name: str) -> int:
        try:
            return self._resolve(collection_name).count()
        except Exception as exc:
            logger.warning("[CHROMA] Could not count '%s': %s", collection_name, exc)
            return 0

    def get_collection(self, collection_name: str) -> chromadb.Collection:
        return self._resolve(collection_name)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _resolve(self, collection_name: str) -> chromadb.Collection:
        """
        Return the collection object, registering it on demand if it is not
        one of the pre-declared COLLECTION_TYPES.  This allows callers to
        use ad-hoc collection names without raising an error.
        """
        if collection_name not in self._collections:
            logger.debug(
                "[CHROMA] Creating on-demand collection '%s'", collection_name
            )
            self._collections[collection_name] = (
                self._client.get_or_create_collection(name=collection_name)
            )
        return self._collections[collection_name]
