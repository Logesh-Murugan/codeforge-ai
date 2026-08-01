"""
ExecutionEvent Model — Phase 5.7
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db import Base


class ExecutionEvent(Base):
    __tablename__ = "execution_events"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    agent_name = Column(String, nullable=True)
    payload_json = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project")
