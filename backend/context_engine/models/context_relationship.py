"""
ContextRelationship Model — Phase 5.5

DB model tracking dependency graphs between context types.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db import Base


class ContextRelationship(Base):
    __tablename__ = "context_relationships"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    source_context_type = Column(String, nullable=False)
    target_context_type = Column(String, nullable=False)
    relationship_strength = Column(Float, default=1.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project")
