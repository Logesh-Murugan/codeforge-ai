"""
ExecutionSummary Model — Phase 5.7
"""
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db import Base


class ExecutionSummary(Base):
    __tablename__ = "execution_summaries"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    total_duration_ms = Column(Float, default=0.0)
    completed_agents_count = Column(Integer, default=13)
    failed_agents_count = Column(Integer, default=0)
    summary_json = Column(JSON, nullable=True)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project")
