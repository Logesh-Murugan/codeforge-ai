"""
TimelineEntry Model — Phase 5.7
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db import Base


class TimelineEntry(Base):
    __tablename__ = "timeline_entries"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    status = Column(String, nullable=False, default="completed")
    duration_ms = Column(Float, default=0.0)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project")
