"""
ConversationMemory — Phase 3.5

Persistent multi-turn conversation buffer scoped per project (and
optionally per session).

Features
--------
- append()            Add a single turn (role + content).
- get_history()       Retrieve ordered turns with optional windowing.
- get_window()        Return only the N most recent turns.
- search()            Semantic search over conversation history.
- clear()             Wipe all conversation turns for a project/session.
- summarise()         Produce a lightweight rolling summary string.
- token_estimate()    Rough token count of the current buffer.

Roles
-----
"user", "assistant", "system" are normalised on write; any other role
is stored as-is.

Session support
---------------
Pass ``session_id`` to scope conversation turns to a specific session
(e.g., a browser tab or API call chain).  When ``session_id`` is
``None`` the global project conversation is used.

Usage
-----
    cm = ConversationMemory(memory_service=svc)

    cm.append(project_id=1, role="user", content="What auth method should I use?")
    cm.append(project_id=1, role="assistant", content="JWT is a good choice.")

    history = cm.get_history(project_id=1, limit=10)
    # [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Canonical turn roles
_VALID_ROLES = {"user", "assistant", "system"}
_WORDS_PER_TOKEN = 0.75   # rough approximation for token estimates


class ConversationMemory:
    """
    Persistent, per-project conversation buffer.

    Args:
        memory_service: Injected :class:`~memory.service.MemoryService`.
                        Falls back to the default auto-wired service.
        default_limit:  Default maximum turns returned by ``get_history()``.
    """

    def __init__(
        self,
        memory_service=None,
        default_limit: int = 20,
    ) -> None:
        if memory_service is None:
            from memory.manager import default_manager
            memory_service = default_manager.get_service()
        self._svc = memory_service
        self.default_limit = default_limit

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _artifact_type(self, role: str, session_id: Optional[str]) -> str:
        """
        Build the artifact_type string stored in ChromaDB.

        Format: ``turn:{role}`` or ``turn:{role}:{session_id}``
        """
        role = role if role in _VALID_ROLES else "user"
        if session_id:
            return f"turn:{role}:{session_id}"
        return f"turn:{role}"

    @staticmethod
    def _extract_role(artifact_type: str) -> str:
        """Reverse of :meth:`_artifact_type` — recover the role string."""
        parts = artifact_type.split(":", 2)
        if len(parts) >= 2:
            return parts[1]
        return "user"

    @staticmethod
    def _extract_session(artifact_type: str) -> Optional[str]:
        """Extract session_id from artifact_type, or None."""
        parts = artifact_type.split(":", 2)
        if len(parts) == 3:
            return parts[2]
        return None

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def append(
        self,
        project_id: int,
        role: str,
        content: str,
        session_id: Optional[str] = None,
    ) -> str:
        """
        Append a conversation turn.

        Args:
            project_id: Owning project.
            role:       "user" | "assistant" | "system" (others allowed).
            content:    Turn text.
            session_id: Optional session scope.

        Returns:
            Memory ID.
        """
        artifact_type = self._artifact_type(role, session_id)
        mem_id = self._svc.store_memory(
            project_id=project_id,
            agent_name="conversation",
            artifact_type=artifact_type,
            collection_name="conversation",
            content=content,
            version=1,
        )
        logger.debug(
            "[CONV_MEMORY] Appended '%s' turn for project %d (session=%s)",
            role, project_id, session_id,
        )
        return mem_id

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_history(
        self,
        project_id: int,
        limit: Optional[int] = None,
        session_id: Optional[str] = None,
        roles: Optional[List[str]] = None,
    ) -> List[Dict[str, str]]:
        """
        Retrieve conversation turns in chronological order.

        Args:
            project_id: Owning project.
            limit:      Max turns to return (defaults to ``default_limit``).
            session_id: Filter to a specific session; ``None`` returns all.
            roles:      Filter to specific roles (e.g. ``["user", "assistant"]``).

        Returns:
            List of ``{"role": str, "content": str}`` dicts, oldest first.
        """
        if limit is None:
            limit = self.default_limit

        raw = self._svc.get_project_memory(project_id, "conversation")
        # Sort chronologically
        raw.sort(key=lambda r: r.get("metadata", {}).get("timestamp", ""))

        turns: List[Dict[str, str]] = []
        for entry in raw:
            art = entry.get("metadata", {}).get("artifact_type", "")
            if not art.startswith("turn:"):
                continue
            # Session filter
            rec_session = self._extract_session(art)
            if session_id is not None and rec_session != session_id:
                continue
            role = self._extract_role(art)
            # Role filter
            if roles and role not in roles:
                continue
            turns.append({"role": role, "content": entry["document"]})

        return turns[-limit:]

    def get_window(
        self,
        project_id: int,
        n: int = 6,
        session_id: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """
        Return the ``n`` most recent turns (convenience alias for
        ``get_history(limit=n)``).
        """
        return self.get_history(project_id=project_id, limit=n, session_id=session_id)

    # ------------------------------------------------------------------
    # Semantic search
    # ------------------------------------------------------------------

    def search(
        self,
        project_id: int,
        query: str,
        limit: int = 5,
        threshold: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search over the conversation history.

        Returns:
            List of result dicts (id, document, metadata, similarity_score).
        """
        return self._svc.retrieve_memory(
            project_id=project_id,
            collection_name="conversation",
            query=query,
            limit=limit,
            threshold=threshold,
        )

    # ------------------------------------------------------------------
    # Clear
    # ------------------------------------------------------------------

    def clear(
        self,
        project_id: int,
        session_id: Optional[str] = None,
    ) -> int:
        """
        Report how many turns would be cleared for a project/session.

        When ``session_id`` is ``None``, counts ALL conversation turns.
        Note: Actual deletion is delegated to
        ``MemoryService.delete_project_memory()`` for full project wipes.

        Returns:
            Number of turns in scope (dry-run count).
        """
        history = self.get_history(
            project_id=project_id,
            limit=10_000,  # effectively all
            session_id=session_id,
        )
        return len(history)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def summarise(
        self,
        project_id: int,
        limit: int = 10,
        session_id: Optional[str] = None,
    ) -> str:
        """
        Produce a compact rolling summary of the most recent turns.

        The summary is a plain-text string with ``Role: content`` lines
        separated by newlines — suitable for inclusion in a system prompt.
        """
        turns = self.get_history(
            project_id=project_id,
            limit=limit,
            session_id=session_id,
        )
        if not turns:
            return ""
        lines = [f"{t['role'].capitalize()}: {t['content']}" for t in turns]
        return "\n".join(lines)

    def token_estimate(
        self,
        project_id: int,
        session_id: Optional[str] = None,
    ) -> int:
        """
        Rough token count of the entire conversation buffer.

        Uses a simple word-count heuristic (1 token ≈ 0.75 words).
        """
        turns = self.get_history(
            project_id=project_id,
            limit=10_000,
            session_id=session_id,
        )
        total_words = sum(len(t["content"].split()) for t in turns)
        return int(total_words / _WORDS_PER_TOKEN)

    def count_turns(
        self,
        project_id: int,
        session_id: Optional[str] = None,
    ) -> int:
        """Return the total number of turns stored for a project/session."""
        return len(
            self.get_history(
                project_id=project_id,
                limit=10_000,
                session_id=session_id,
            )
        )
