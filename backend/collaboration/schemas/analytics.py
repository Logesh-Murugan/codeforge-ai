"""
Analytics Schemas — Phase 5.4

Pydantic data models for collaboration reporting, status, relationship maps, and metrics.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ActiveCollaboratorStatus(BaseModel):
    agent_name: str
    status: str = "idle"  # idle, communicating, validating, waiting
    last_action: Optional[str] = None
    last_active: Optional[datetime] = None


class CollaborationStatusResponse(BaseModel):
    """Real-time status of active collaborators for a project."""

    project_id: int
    active_collaborators: List[ActiveCollaboratorStatus]
    total_interactions: int
    current_phase: str = "active"
    overall_health: str = "healthy"


class AgentRelationshipEdge(BaseModel):
    source: str
    target: str
    interaction_count: int
    agreement_score: float
    weight: float = 1.0


class RelationshipMapResponse(BaseModel):
    """Dependency matrix and relationship network between agents."""

    project_id: int
    agents: List[str]
    relationships: List[AgentRelationshipEdge]
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CollaborationReportResponse(BaseModel):
    """Comprehensive collaboration report for a project."""

    project_id: int
    overall_score: float
    consensus_rating: float
    information_density: float
    friction_score: float
    total_messages: int
    total_validations: int
    total_feedback_entries: int
    execution_trace_id: Optional[str] = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
