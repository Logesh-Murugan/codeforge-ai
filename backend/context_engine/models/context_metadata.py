"""
ContextMetadata Model — Phase 5.5

DB model for storing context entities, types, versions, and payloads.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db import Base


class ContextMetadata(Base):
    __tablename__ = "context_metadata"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    context_type = Column(String, nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    producer_agent = Column(String, nullable=False, default="system")
    payload_json = Column(JSON, nullable=True)
    status = Column(String, nullable=False, default="valid")  # valid, invalid, expired, corrupted
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    project = relationship("Project")
