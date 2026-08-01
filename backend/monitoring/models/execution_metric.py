"""
ExecutionMetric Model — Phase 5.7
"""
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db import Base


class ExecutionMetric(Base):
    __tablename__ = "execution_metrics"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    execution_time_ms = Column(Float, default=0.0)
    avg_agent_runtime_ms = Column(Float, default=0.0)
    workflow_runtime_ms = Column(Float, default=0.0)
    retry_count = Column(Integer, default=0)
    success_rate = Column(Float, default=1.0)
    failure_rate = Column(Float, default=0.0)
    token_estimate = Column(Integer, default=0)
    generated_files_count = Column(Integer, default=0)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project")
