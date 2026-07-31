"""
ContextScore Model — Phase 5.5

DB model for storing 6-tier quality score metrics per context entity.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db import Base


class ContextScore(Base):
    __tablename__ = "context_scores"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    context_type = Column(String, nullable=False)
    relevancy_score = Column(Float, default=1.0)
    confidence_score = Column(Float, default=1.0)
    priority_score = Column(Float, default=1.0)
    freshness_score = Column(Float, default=1.0)
    source_score = Column(Float, default=1.0)
    overall_quality_score = Column(Float, default=1.0)
    evaluated_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project")
