"""
MemoryEmbeddingRecord — Phase 5.1

Links PostgreSQL persistent memory entries to their ChromaDB vector
representations.  This bridge table enables bi-directional lookup:

  PostgreSQL entry ←→ ChromaDB document

Storage: PostgreSQL via ``app.db.Base``.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Integer, DateTime, ForeignKey,
)

from app.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MemoryEmbeddingRecord(Base):
    """
    Tracks the linkage between a persistent memory entry (PostgreSQL)
    and its vector embedding document(s) in ChromaDB.

    One memory entry may map to multiple ChromaDB documents if the
    content was chunked during embedding.
    """
    __tablename__ = "memory_embedding_records"

    id = Column(Integer, primary_key=True, index=True)
    memory_entry_id = Column(
        Integer,
        ForeignKey("persistent_project_memory.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chroma_collection = Column(String(100), nullable=False)
    chroma_doc_id = Column(String(200), nullable=False, index=True)
    embedding_provider = Column(String(50), nullable=False, default="local")
    chunk_index = Column(Integer, nullable=False, default=0)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=_utcnow,
    )
