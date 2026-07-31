"""
CollaborationLog Model — Phase 5.4

DB model for logging agent-to-agent message exchanges and context traces.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db import Base


class CollaborationLog(Base):
    __tablename__ = "collaboration_logs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    sender_agent = Column(String, nullable=False)
    receiver_agent = Column(String, nullable=False)
    pattern = Column(String, nullable=False, default="sequential")  # sequential, parallel, validation, feedback
    payload_json = Column(JSON, nullable=True)
    status = Column(String, nullable=False, default="sent")  # sent, acknowledged, validated, rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project")
