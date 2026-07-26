"""
LongTermMemory — Phase 3.5

Decay-weighted semantic retrieval that ranks results by a combination of:
  - Semantic similarity score
  - Recency (exponential decay on age)
  - Explicit importance weight (stored in metadata)

This surfaces recently created, high-importance records above stale,
low-confidence ones — mimicking long-term human memory.

Decay function
--------------
    adjusted_score = similarity * recency_weight * importance
    recency_weight = exp(-decay_rate * age_hours)

Usage
-----
    ltm = LongTermMemory(memory_service=svc, decay_rate=0.01)
    results = ltm.retrieve(
        project_id=1,
        query="JWT authentication",
        collections=["backend_code", "requirements"],
        limit=5,
    )
"""
from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_DEFAULT_DECAY_RATE = 0.005   # per hour — mild decay so week-old records still surface
_DEFAULT_IMPORTANCE  = 1.0    # neutral weight when not set in metadata


def _parse_iso(ts: str) -> Optional[datetime]:
    """Parse an ISO-8601 string to a timezone-aware datetime, return None on failure."""
    try:
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _recency_weight(timestamp_iso: str, decay_rate: float) -> float:
    """
    Compute the recency factor for a record.

    Returns a value in (0, 1] where 1.0 means "just created".
    """
    dt = _parse_iso(timestamp_iso)
    if dt is None:
        return 1.0  # unknown age — treat as fresh
    now = datetime.now(timezone.utc)
    age_hours = max(0.0, (now - dt).total_seconds() / 3600.0)
    return math.exp(-decay_rate * age_hours)


class LongTermMemory:
    """
    Decay-weighted semantic retrieval over project memory.

    Args:
        memory_service: Injected :class:`~memory.service.MemoryService`.
                        Falls back to the default auto-wired service.
        decay_rate:     Per-hour exponential decay constant.
                        0.005 → a 1-week-old record retains ~66% weight.
                        0.01  → a 1-week-old record retains ~44% weight.
    """

    def __init__(
        self,
        memory_service=None,
        decay_rate: float = _DEFAULT_DECAY_RATE,
    ) -> None:
        if memory_service is None:
            from memory.manager import default_manager
            memory_service = default_manager.get_service()
        self._svc = memory_service
        self.decay_rate = decay_rate

    # ------------------------------------------------------------------
    # Store with importance weight
    # ------------------------------------------------------------------

    def store(
        self,
        project_id: int,
        agent_name: str,
        artifact_type: str,
        collection_name: str,
        content: str,
        version: int = 1,
        importance: float = 1.0,
    ) -> str:
        """
        Store a memory record.

        ``importance`` is a multiplier [0.1 – 5.0] that biases later
        retrieval.  Values > 1.0 surface the record more readily; < 1.0
        de-prioritise it.

        Returns:
            Memory ID.
        """
        # Clamp importance to a sensible range
        importance = max(0.1, min(5.0, importance))
        # We embed importance in the content prefix so it's retrievable
        # even without custom metadata support.
        tagged = f"[importance={importance:.2f}] {content}"
        return self._svc.store_memory(
            project_id=project_id,
            agent_name=agent_name,
            artifact_type=artifact_type,
            collection_name=collection_name,
            content=tagged,
            version=version,
        )

    # ------------------------------------------------------------------
    # Retrieve with decay weighting
    # ------------------------------------------------------------------

    def retrieve(
        self,
        project_id: int,
        query: str,
        collections: Optional[List[str]] = None,
        limit: int = 5,
        threshold: float = 0.0,
        min_recency_weight: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Semantic retrieval with recency and importance re-ranking.

        Args:
            project_id:         Owning project.
            query:              Natural-language query.
            collections:        Collections to search. ``None`` → all domain
                                collections.
            limit:              Max results returned (after re-ranking).
            threshold:          Minimum raw similarity score before decay.
            min_recency_weight: Discard records whose recency weight is below
                                this value (0.0 = no filter).

        Returns:
            List of result dicts with an additional ``adjusted_score`` key.
        """
        from memory.vectorstores.chroma import ChromaVectorStore

        if collections is None:
            collections = [
                c for c in ChromaVectorStore.COLLECTION_TYPES
                if c not in ("conversation",)
            ]

        raw_results: List[Dict[str, Any]] = []
        for col in collections:
            try:
                hits = self._svc.retrieve_memory(
                    project_id=project_id,
                    collection_name=col,
                    query=query,
                    limit=limit * 2,   # over-fetch before re-ranking
                    threshold=threshold,
                )
                for h in hits:
                    h["_collection"] = col
                    raw_results.append(h)
            except Exception as exc:
                logger.debug("[LTM] Skipping collection '%s': %s", col, exc)

        # Re-rank
        ranked: List[Dict[str, Any]] = []
        for r in raw_results:
            ts = r.get("metadata", {}).get("timestamp", "")
            rw = _recency_weight(ts, self.decay_rate)
            if rw < min_recency_weight:
                continue
            # Extract importance from content prefix if present
            importance = _DEFAULT_IMPORTANCE
            doc: str = r.get("document", "")
            if doc.startswith("[importance="):
                try:
                    imp_str = doc[len("[importance="):doc.index("]")]
                    importance = float(imp_str)
                    # Strip the tag from the exposed document
                    r["document"] = doc[doc.index("]") + 2:]
                except (ValueError, IndexError):
                    pass

            sim = r.get("similarity_score", 0.0)
            r["adjusted_score"] = sim * rw * importance
            r["recency_weight"] = rw
            r["importance"] = importance
            ranked.append(r)

        ranked.sort(key=lambda x: x["adjusted_score"], reverse=True)
        return ranked[:limit]

    # ------------------------------------------------------------------
    # Forget — remove outdated records below a recency threshold
    # ------------------------------------------------------------------

    def forget_stale(
        self,
        project_id: int,
        collection_name: str,
        min_recency_weight: float = 0.1,
    ) -> int:
        """
        Report (but do NOT delete) how many records in *collection_name*
        fall below *min_recency_weight*.

        Deletion is intentionally left to the caller — this method acts
        as a "what would be forgotten" dry-run.

        Returns:
            Count of stale records.
        """
        raw = self._svc.get_project_memory(project_id, collection_name)
        stale = 0
        for item in raw:
            ts = item.get("metadata", {}).get("timestamp", "")
            rw = _recency_weight(ts, self.decay_rate)
            if rw < min_recency_weight:
                stale += 1
        return stale
