"""
CollaborationScore Model — Phase 5.4

DB model storing overall collaboration scores, consensus index, and execution traces.
"""
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db import Base


class CollaborationScore(Base):
    __tablename__ = "collaboration_scores"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    overall_score = Column(Float, default=1.0)
    consensus_rating = Column(Float, default=1.0)
    information_density = Column(Float, default=1.0)
    friction_score = Column(Float, default=0.0)
    execution_trace_id = Column(String, nullable=True)
    details_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project")
