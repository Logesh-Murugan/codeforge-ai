"""
ProjectMemoryService — Phase 3.4

High-level service for all project-scoped memory operations.

Responsibilities
----------------
- store_requirement()      Store or version-bump a requirements artifact.
- store_architecture()     Store or version-bump an architecture artifact.
- store_generated_file()   Track a generated source file with path + language.
- store_agent_output()     Record any agent's output into its canonical collection.
- record_revision()        Append a tracked revision with a reason and author.
- get_agent_memory()       Retrieve all outputs for a specific agent.
- get_version_history()    Fetch all versioned snapshots for an artifact type.
- get_generated_files()    List all generated files recorded for a project.
- get_revisions()          List all revision records for a project.
- get_project_snapshot()   Build a full ProjectSnapshot for a project.
- search_project_memory()  Cross-collection semantic search within a project.

All storage is delegated to the injected ``MemoryService`` instance so this
service stays thin — it only adds project-memory semantics on top.
"""
from __future__ import annotations

import datetime
import logging
import uuid
from typing import Any, Dict, List, Optional

from memory.schemas import (
    AgentMemoryRecord,
    GeneratedFileRecord,
    ProjectHistoryEntry,
    ProjectSnapshot,
    RevisionEntry,
)

logger = logging.getLogger(__name__)

# Mapping from artifact_type string → canonical ChromaDB collection name
_ARTIFACT_COLLECTION: Dict[str, str] = {
    "requirements":     "requirements",
    "architecture":     "architecture",
    "database_design":  "database_design",
    "api_contracts":    "api_contracts",
    "backend_code":     "backend_code",
    "frontend_code":    "frontend_code",
    "security_report":  "security_reports",
    "qa_report":        "qa_reports",
    "documentation":    "documentation",
    "devops":           "devops",
    "generated_file":   "backend_code",   # files go to their code collection
    "agent_output":     "project_history",
    "revision":         "project_history",
}

# Collections that hold generated code artifacts
_CODE_COLLECTIONS = {"backend_code", "frontend_code"}


def _now_iso() -> str:
    return datetime.datetime.utcnow().isoformat()


class ProjectMemoryService:
    """
    Project-centric memory façade.

    Args:
        memory_service: Injected :class:`~memory.service.MemoryService`.
                        When ``None``, the default auto-wired service is used.
    """

    def __init__(self, memory_service=None) -> None:
        if memory_service is None:
            from memory.manager import default_manager
            memory_service = default_manager.get_service()
        self._svc = memory_service
        logger.info("[PROJECT_MEMORY] ProjectMemoryService ready")

    # ======================================================================
    # Requirement memory
    # ======================================================================

    def store_requirement(
        self,
        project_id: int,
        content: str,
        version: int = 1,
        agent_name: str = "requirements_analyst",
    ) -> str:
        """
        Store a requirements artifact and mirror it into project_history.

        Returns:
            Memory ID of the first stored chunk.
        """
        mem_id = self._svc.store_memory(
            project_id=project_id,
            agent_name=agent_name,
            artifact_type="requirements",
            collection_name="requirements",
            content=content,
            version=version,
        )
        self._svc.record_version(
            project_id=project_id,
            agent_name=agent_name,
            artifact_type="requirements",
            content=content,
            version=version,
        )
        logger.info(
            "[PROJECT_MEMORY] Stored requirements v%d for project %d → %s",
            version, project_id, mem_id,
        )
        return mem_id

    # ======================================================================
    # Architecture memory
    # ======================================================================

    def store_architecture(
        self,
        project_id: int,
        content: str,
        artifact_type: str = "architecture",
        version: int = 1,
        agent_name: str = "architect",
    ) -> str:
        """
        Store an architecture artifact (architecture / database_design /
        api_contracts) and mirror it into project_history.
        """
        collection = _ARTIFACT_COLLECTION.get(artifact_type, "architecture")
        mem_id = self._svc.store_memory(
            project_id=project_id,
            agent_name=agent_name,
            artifact_type=artifact_type,
            collection_name=collection,
            content=content,
            version=version,
        )
        self._svc.record_version(
            project_id=project_id,
            agent_name=agent_name,
            artifact_type=artifact_type,
            content=content,
            version=version,
        )
        logger.info(
            "[PROJECT_MEMORY] Stored architecture '%s' v%d for project %d → %s",
            artifact_type, version, project_id, mem_id,
        )
        return mem_id

    # ======================================================================
    # Generated code / file memory
    # ======================================================================

    def store_generated_file(
        self,
        project_id: int,
        file_path: str,
        content: str,
        language: str = "python",
        agent_name: str = "backend_developer",
        version: int = 1,
    ) -> str:
        """
        Record a generated source file with its path and language.

        The file is stored in the appropriate code collection and mirrored
        into ``project_history`` with ``artifact_type="generated_file"``.
        """
        # Choose collection based on language hint
        if language in ("typescript", "tsx", "jsx", "javascript", "css", "html"):
            collection = "frontend_code"
        else:
            collection = "backend_code"

        # Prefix content with the file path so retrieval returns context
        tagged_content = f"# File: {file_path}\n{content}"

        mem_id = self._svc.store_memory(
            project_id=project_id,
            agent_name=agent_name,
            artifact_type="generated_file",
            collection_name=collection,
            content=tagged_content,
            version=version,
        )
        self._svc.record_version(
            project_id=project_id,
            agent_name=agent_name,
            artifact_type="generated_file",
            content=tagged_content,
            version=version,
        )
        logger.info(
            "[PROJECT_MEMORY] Stored generated file '%s' (%s) v%d for project %d",
            file_path, language, version, project_id,
        )
        return mem_id

    # ======================================================================
    # Agent output memory
    # ======================================================================

    def store_agent_output(
        self,
        project_id: int,
        agent_name: str,
        artifact_type: str,
        content: str,
        version: int = 1,
    ) -> str:
        """
        Store any agent's output in its canonical collection and mirror it
        into ``project_history``.
        """
        collection = _ARTIFACT_COLLECTION.get(artifact_type, "project_history")
        mem_id = self._svc.store_memory(
            project_id=project_id,
            agent_name=agent_name,
            artifact_type=artifact_type,
            collection_name=collection,
            content=content,
            version=version,
        )
        self._svc.record_version(
            project_id=project_id,
            agent_name=agent_name,
            artifact_type=artifact_type,
            content=content,
            version=version,
        )
        logger.info(
            "[PROJECT_MEMORY] Stored agent output '%s/%s' v%d for project %d",
            agent_name, artifact_type, version, project_id,
        )
        return mem_id

    # ======================================================================
    # Revision tracking
    # ======================================================================

    def record_revision(
        self,
        project_id: int,
        artifact_type: str,
        content: str,
        version: int = 1,
        reason: str = "",
        requested_by: str = "system",
    ) -> str:
        """
        Record a tracked revision with an optional reason and author.

        Revisions are stored in ``project_history`` with enriched metadata.
        """
        revision_id = str(uuid.uuid4())
        tagged_content = (
            f"[REVISION] artifact_type={artifact_type} "
            f"version={version} reason={reason!r} "
            f"requested_by={requested_by}\n\n{content}"
        )
        mem_id = self._svc.record_version(
            project_id=project_id,
            agent_name=requested_by,
            artifact_type=f"revision:{artifact_type}",
            content=tagged_content,
            version=version,
        )
        logger.info(
            "[PROJECT_MEMORY] Recorded revision for '%s' v%d (project %d) → %s",
            artifact_type, version, project_id, mem_id,
        )
        return mem_id

    # ======================================================================
    # Retrieval helpers
    # ======================================================================

    def get_agent_memory(
        self,
        project_id: int,
        agent_name: str,
        collection_name: Optional[str] = None,
    ) -> List[AgentMemoryRecord]:
        """
        Return all memory records produced by a specific agent.

        If ``collection_name`` is not given, searches ``project_history``.
        """
        col = collection_name or "project_history"
        raw = self._svc.get_project_memory(project_id, col)
        records: List[AgentMemoryRecord] = []
        for item in raw:
            meta = item.get("metadata", {})
            if meta.get("agent_name") != agent_name:
                continue
            try:
                records.append(
                    AgentMemoryRecord(
                        id=item["id"],
                        project_id=project_id,
                        agent_name=meta.get("agent_name", agent_name),
                        artifact_type=meta.get("artifact_type", ""),
                        collection_name=col,
                        content=item["document"],
                        version=int(meta.get("version", 1)),
                        timestamp=datetime.datetime.fromisoformat(
                            meta.get("timestamp", _now_iso())
                        ),
                        metadata=meta,
                    )
                )
            except Exception as exc:
                logger.debug("[PROJECT_MEMORY] Skipping malformed record: %s", exc)
        records.sort(key=lambda r: r.version)
        return records

    def get_version_history(
        self,
        project_id: int,
        artifact_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[ProjectHistoryEntry]:
        """
        Fetch all versioned snapshots, optionally filtered by artifact_type.
        """
        entries = self._svc.get_version_history(project_id, artifact_type)
        return entries[:limit]

    def get_generated_files(
        self,
        project_id: int,
    ) -> List[GeneratedFileRecord]:
        """
        Return all generated file records for a project from both code
        collections.
        """
        files: List[GeneratedFileRecord] = []
        for col in ("backend_code", "frontend_code"):
            raw = self._svc.get_project_memory(project_id, col)
            for item in raw:
                meta = item.get("metadata", {})
                if meta.get("artifact_type") != "generated_file":
                    continue
                content = item["document"]
                # Extract the file_path from the tagged prefix
                file_path = ""
                if content.startswith("# File: "):
                    first_line, _, rest = content.partition("\n")
                    file_path = first_line.replace("# File: ", "").strip()
                    content = rest
                try:
                    lang = "typescript" if col == "frontend_code" else "python"
                    files.append(
                        GeneratedFileRecord(
                            id=item["id"],
                            project_id=project_id,
                            file_path=file_path,
                            language=lang,
                            content=content,
                            agent_name=meta.get("agent_name", ""),
                            version=int(meta.get("version", 1)),
                            timestamp=datetime.datetime.fromisoformat(
                                meta.get("timestamp", _now_iso())
                            ),
                        )
                    )
                except Exception as exc:
                    logger.debug("[PROJECT_MEMORY] Skipping malformed file record: %s", exc)
        files.sort(key=lambda f: (f.file_path, f.version))
        return files

    def get_revisions(
        self,
        project_id: int,
        artifact_type: Optional[str] = None,
    ) -> List[RevisionEntry]:
        """
        Return all revision records for a project, optionally filtered by
        artifact_type.
        """
        prefix = f"revision:{artifact_type}" if artifact_type else "revision:"
        raw = self._svc.get_project_memory(project_id, "project_history")
        revisions: List[RevisionEntry] = []
        for item in raw:
            meta = item.get("metadata", {})
            stored_type = meta.get("artifact_type", "")
            if not stored_type.startswith(prefix):
                continue
            try:
                revisions.append(
                    RevisionEntry(
                        id=item["id"],
                        project_id=project_id,
                        artifact_type=stored_type.replace("revision:", "", 1),
                        version=int(meta.get("version", 1)),
                        content=item["document"],
                        timestamp=datetime.datetime.fromisoformat(
                            meta.get("timestamp", _now_iso())
                        ),
                    )
                )
            except Exception as exc:
                logger.debug("[PROJECT_MEMORY] Skipping malformed revision: %s", exc)
        revisions.sort(key=lambda r: (r.artifact_type, r.version))
        return revisions

    # ======================================================================
    # Snapshot
    # ======================================================================

    def get_project_snapshot(self, project_id: int) -> ProjectSnapshot:
        """
        Build a full ``ProjectSnapshot`` for a project.

        This is an aggregate read — it fetches every category of memory in
        one call.  Use sparingly on large projects; prefer targeted getters
        for performance-sensitive paths.
        """
        req_raw = self._svc.get_project_memory(project_id, "requirements")
        arch_raw = self._svc.get_project_memory(project_id, "architecture")

        def _to_agent_records(
            raw: List[Dict[str, Any]], col: str
        ) -> List[AgentMemoryRecord]:
            out: List[AgentMemoryRecord] = []
            for item in raw:
                meta = item.get("metadata", {})
                try:
                    out.append(
                        AgentMemoryRecord(
                            id=item["id"],
                            project_id=project_id,
                            agent_name=meta.get("agent_name", ""),
                            artifact_type=meta.get("artifact_type", ""),
                            collection_name=col,
                            content=item["document"],
                            version=int(meta.get("version", 1)),
                            timestamp=datetime.datetime.fromisoformat(
                                meta.get("timestamp", _now_iso())
                            ),
                            metadata=meta,
                        )
                    )
                except Exception as exc:
                    logger.debug("[PROJECT_MEMORY] Snapshot: skipping record: %s", exc)
            return out

        return ProjectSnapshot(
            project_id=project_id,
            requirements=_to_agent_records(req_raw, "requirements"),
            architecture=_to_agent_records(arch_raw, "architecture"),
            generated_files=self.get_generated_files(project_id),
            agent_outputs=_to_agent_records(
                self._svc.get_project_memory(project_id, "project_history"),
                "project_history",
            ),
            revisions=self.get_revisions(project_id),
            version_history=self.get_version_history(project_id),
        )

    # ======================================================================
    # Semantic search
    # ======================================================================

    def search_project_memory(
        self,
        project_id: int,
        query: str,
        collections: Optional[List[str]] = None,
        limit: int = 5,
        threshold: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search across all (or selected) project collections.
        """
        from memory.vectorstores.chroma import ChromaVectorStore

        if collections is None:
            collections = [
                c for c in ChromaVectorStore.COLLECTION_TYPES
                if c not in ("conversation",)
            ]

        results: List[Dict[str, Any]] = []
        for col in collections:
            hits = self._svc.retrieve_memory(
                project_id=project_id,
                collection_name=col,
                query=query,
                limit=limit,
                threshold=threshold,
            )
            for hit in hits:
                hit["collection"] = col
                results.append(hit)

        results.sort(key=lambda r: r.get("similarity_score", 0.0), reverse=True)
        return results[:limit]
