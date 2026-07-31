"""
AgentRelationship Model — Phase 5.4

DB model tracking relationships, interaction counts, and agreement metrics between agents.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db import Base


class AgentRelationship(Base):
    __tablename__ = "agent_relationships"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    source_agent = Column(String, nullable=False)
    target_agent = Column(String, nullable=False)
    interaction_count = Column(Integer, default=1)
    agreement_score = Column(Float, default=1.0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    project = relationship("Project")
