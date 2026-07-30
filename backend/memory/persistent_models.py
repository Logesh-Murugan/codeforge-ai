"""
Persistent Memory SQLAlchemy models — Phase 5.1

Two tables:
  persistent_project_memory   — Project-scoped memory entries with category.
  persistent_memory_versions  — Immutable version history for each entry.

All storage is PostgreSQL via app.db.AsyncSessionLocal.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, JSON

from app.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


class PersistentProjectMemory(Base):
    __tablename__ = "persistent_project_memory"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False, default="system")
    content = Column(Text, nullable=False)
    metadata_json = Column(JSON, default=dict)
    version = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PersistentMemoryVersion(Base):
    __tablename__ = "persistent_memory_versions"

    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(Integer, ForeignKey("persistent_project_memory.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    metadata_json = Column(JSON, default=dict)
    version = Column(Integer, nullable=False)
    change_reason = Column(String(500), default="")
    changed_by = Column(String(100), default="system")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
