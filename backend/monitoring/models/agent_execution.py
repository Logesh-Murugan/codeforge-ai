"""
AgentExecution Model — Phase 5.7
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db import Base


class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflow_executions.id"), nullable=False, index=True)
    agent_name = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default="waiting")  # waiting, running, retrying, completed, failed, cancelled
    execution_time_ms = Column(Float, default=0.0)
    retry_count = Column(Integer, default=0)
    current_task = Column(String, nullable=True)
    input_size = Column(Integer, default=0)
    output_size = Column(Integer, default=0)
    generated_files_count = Column(Integer, default=0)
    validation_score = Column(Float, default=1.0)
    security_score = Column(Float, default=1.0)
    documentation_score = Column(Float, default=1.0)
    quality_score = Column(Float, default=1.0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    workflow = relationship("WorkflowExecution")
