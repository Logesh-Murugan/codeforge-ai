"""
ValidationRun Model — Phase 5.8
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db import Base


class ValidationRun(Base):
    __tablename__ = "validation_runs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    status = Column(String, nullable=False, default="PASSED")  # PASSED, WARNING, FAILED
    score = Column(Float, default=100.0)
    quality_grade = Column(String, default="A+")
    duration_ms = Column(Float, default=0.0)
    executed_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project")
