"""
ContextReport Model — Phase 5.5

DB model storing project-level context audit reports.
"""
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db import Base


class ContextReport(Base):
    __tablename__ = "context_reports"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    total_contexts = Column(Integer, default=0)
    valid_contexts = Column(Integer, default=0)
    invalid_contexts = Column(Integer, default=0)
    average_quality_score = Column(Float, default=1.0)
    summary_json = Column(JSON, nullable=True)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project")
