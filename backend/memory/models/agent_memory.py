"""
AgentMemoryEntry — Phase 5.1

Tracks agent-specific memory entries with execution context and output
summaries.  Each row captures one agent's contribution to a project's
persistent memory, with optional links to the parent
``persistent_project_memory`` entry.

Storage: PostgreSQL via ``app.db.Base``.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Text, Integer, Boolean, DateTime,
    ForeignKey, JSON, Float,
)

from app.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


class AgentMemoryEntry(Base):
    """
    Persistent record of a single agent's memory contribution.

    Complements ``PersistentProjectMemory`` with agent-execution-specific
    metadata such as task context, execution duration, and model info.
    """
    __tablename__ = "agent_memory_entries"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    memory_entry_id = Column(
        Integer,
        ForeignKey("persistent_project_memory.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    agent_name = Column(String(100), nullable=False, index=True)
    agent_type = Column(String(50), nullable=False, default="general")
    task_context = Column(Text, nullable=True)
    output_summary = Column(Text, nullable=True)
    execution_metadata = Column(JSON, default=dict)
    model_used = Column(String(100), nullable=True)
    execution_duration_ms = Column(Float, nullable=True)
    token_count = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=_utcnow,
    )
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow,
    )
