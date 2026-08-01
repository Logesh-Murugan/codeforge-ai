"""
ValidationScore Model — Phase 5.8
"""
from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.db import Base


class ValidationScore(Base):
    __tablename__ = "validation_scores"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("validation_runs.id"), nullable=False, index=True)
    structure_score = Column(Float, default=100.0)
    syntax_score = Column(Float, default=100.0)
    dependency_score = Column(Float, default=100.0)
    architecture_score = Column(Float, default=100.0)
    database_score = Column(Float, default=100.0)
    api_score = Column(Float, default=100.0)
    security_score = Column(Float, default=100.0)
    documentation_score = Column(Float, default=100.0)
    docker_score = Column(Float, default=100.0)
    testing_score = Column(Float, default=100.0)
    performance_score = Column(Float, default=100.0)
    code_quality_score = Column(Float, default=100.0)
    overall_score = Column(Float, default=100.0)

    run = relationship("ValidationRun")
