"""
ContextHistory Model — Phase 5.5

DB model for logging context creation, updates, producers, consumers, and changes.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db import Base


class ContextHistory(Base):
    __tablename__ = "context_history"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    context_id = Column(Integer, ForeignKey("context_metadata.id"), nullable=True)
    context_type = Column(String, nullable=False)
    producer_agent = Column(String, nullable=False)
    consumer_agent = Column(String, nullable=True)
    action = Column(String, nullable=False)  # created, updated, consumed, invalidated, routed
    version = Column(Integer, default=1)
    change_summary = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project")
