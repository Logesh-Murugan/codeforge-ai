"""
WorkflowExecution Model — Phase 5.7
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db import Base


class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    status = Column(String, nullable=False, default="pending")  # pending, running, completed, failed, cancelled
    current_step = Column(String, nullable=True)
    completed_steps = Column(Integer, default=0)
    failed_steps = Column(Integer, default=0)
    progress_pct = Column(Float, default=0.0)
    execution_duration = Column(Float, default=0.0)
    estimated_remaining_time = Column(Float, default=0.0)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    project = relationship("Project")
