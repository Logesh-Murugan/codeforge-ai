"""
CrossAgentMemory — Phase 3.5

A read/write shared memory bus that lets any agent in the pipeline
inspect the outputs of any other agent for the same project.

Key design choices
------------------
- Writes are always mirrored into project_history for auditability.
- Reads use the collection routing table from ProjectMemoryService to
  find the right collection for each artifact_type.
- ``broadcast()`` is a convenience that writes once and immediately
  makes the data available to all consumers.

Usage
-----
    cam = CrossAgentMemory(memory_service=svc)

    # security_engineer publishes its findings:
    cam.publish(
        project_id=1,
        agent_name="security_engineer",
        artifact_type="security_report",
        content="## Security Report ...",
        version=1,
    )

    # qa_engineer reads it:
    reports = cam.read(
        project_id=1,
        source_agent="security_engineer",
        artifact_type="security_report",
    )
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Canonical mapping of artifact_type → collection name
# (mirrors the mapping in ProjectMemoryService)
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
    "generated_file":   "backend_code",
    "agent_output":     "project_history",
    "revision":         "project_history",
}


class CrossAgentMemory:
    """
    Shared memory bus — lets agents read each other's outputs.

    Args:
        memory_service: Injected :class:`~memory.service.MemoryService`.
                        Falls back to the default auto-wired service.
    """

    def __init__(self, memory_service=None) -> None:
        if memory_service is None:
            from memory.manager import default_manager
            memory_service = default_manager.get_service()
        self._svc = memory_service

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def publish(
        self,
        project_id: int,
        agent_name: str,
        artifact_type: str,
        content: str,
        version: int = 1,
    ) -> str:
        """
        Write an agent artifact so that other agents can read it.

        The artifact is stored in the canonical collection *and* mirrored
        into ``project_history``.

        Returns:
            Memory ID.
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
        # Mirror to project_history
        self._svc.record_version(
            project_id=project_id,
            agent_name=agent_name,
            artifact_type=artifact_type,
            content=content,
            version=version,
        )
        logger.info(
            "[CROSS_AGENT] Published '%s/%s' v%d → %s (project %d)",
            agent_name, artifact_type, version, mem_id, project_id,
        )
        return mem_id

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def read(
        self,
        project_id: int,
        source_agent: Optional[str] = None,
        artifact_type: Optional[str] = None,
        collection_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Read artifacts from a shared collection.

        Filtering:
        - ``source_agent``:  Only return records produced by this agent.
        - ``artifact_type``: Only return records of this type.
        - ``collection_name``: Override the auto-resolved collection.

        Returns:
            List of raw record dicts (id, document, metadata).
        """
        # Resolve collection
        col = collection_name
        if col is None and artifact_type:
            col = _ARTIFACT_COLLECTION.get(artifact_type, "project_history")
        if col is None:
            col = "project_history"

        raw = self._svc.get_project_memory(project_id, col)

        # Apply filters
        results: List[Dict[str, Any]] = []
        for item in raw:
            meta = item.get("metadata", {})
            if source_agent and meta.get("agent_name") != source_agent:
                continue
            if artifact_type and meta.get("artifact_type") != artifact_type:
                continue
            results.append(item)

        return results

    def read_latest(
        self,
        project_id: int,
        source_agent: str,
        artifact_type: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Return the highest-version record produced by *source_agent* for
        *artifact_type*, or ``None`` if no record exists.
        """
        records = self.read(
            project_id=project_id,
            source_agent=source_agent,
            artifact_type=artifact_type,
        )
        if not records:
            return None
        # Sort by version descending, take the first
        records.sort(
            key=lambda r: int(r.get("metadata", {}).get("version", 0)),
            reverse=True,
        )
        return records[0]

    # ------------------------------------------------------------------
    # Broadcast — write + immediate return of the record
    # ------------------------------------------------------------------

    def broadcast(
        self,
        project_id: int,
        agent_name: str,
        artifact_type: str,
        content: str,
        version: int = 1,
    ) -> Dict[str, Any]:
        """
        Publish *content* and return the record so callers can chain.

        Returns:
            Dict with ``mem_id``, ``agent_name``, ``artifact_type``,
            ``version``, ``project_id``.
        """
        mem_id = self.publish(
            project_id=project_id,
            agent_name=agent_name,
            artifact_type=artifact_type,
            content=content,
            version=version,
        )
        return {
            "mem_id": mem_id,
            "project_id": project_id,
            "agent_name": agent_name,
            "artifact_type": artifact_type,
            "version": version,
        }

    # ------------------------------------------------------------------
    # List available agents
    # ------------------------------------------------------------------

    def list_agents(self, project_id: int) -> List[str]:
        """
        Return the distinct set of agent names that have published to
        *project_id*.
        """
        raw = self._svc.get_project_memory(project_id, "project_history")
        agents = {
            item.get("metadata", {}).get("agent_name", "")
            for item in raw
            if item.get("metadata", {}).get("agent_name")
        }
        return sorted(agents)
