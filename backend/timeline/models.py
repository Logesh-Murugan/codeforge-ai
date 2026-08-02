"""
Timeline Models — Phase 5.9
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db import Base


class TimelineEventModel(Base):
    __tablename__ = "timeline_event_history"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    event_id = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    agent_name = Column(String, nullable=True, index=True)
    stage_name = Column(String, nullable=True, index=True)
    status = Column(String, nullable=False, default="COMPLETED")  # STARTED, COMPLETED, FAILED, RETRYING
    duration_ms = Column(Float, default=0.0)
    retry_count = Column(Integer, default=0)
    model_used = Column(String, nullable=True)
    provider_used = Column(String, nullable=True)
    execution_cost = Column(Float, default=0.0)
    execution_time_ms = Column(Float, default=0.0)
    generated_files_count = Column(Integer, default=0)
    validation_score = Column(Float, default=1.0)
    error_message = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)

    project = relationship("Project")


class MilestoneModel(Base):
    __tablename__ = "timeline_milestones"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    milestone_name = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default="ACHIEVED")  # PENDING, IN_PROGRESS, ACHIEVED
    achieved_at = Column(DateTime(timezone=True), server_default=func.now())
    details_json = Column(JSON, nullable=True)

    project = relationship("Project")
