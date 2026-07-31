"""
Analytics Schemas — Phase 5.5

Pydantic data models for visualization, history, and audit reports.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ContextHistoryRecord(BaseModel):
    id: int
    project_id: int
    context_type: str
    producer_agent: str
    consumer_agent: Optional[str] = None
    action: str
    version: int
    timestamp: datetime


class ContextFlowGraphNode(BaseModel):
    id: str
    label: str
    context_type: str
    status: str = "valid"


class ContextFlowGraphEdge(BaseModel):
    source: str
    target: str
    label: str = "flows_to"


class ContextVisualizationResponse(BaseModel):
    """Data payload for frontend context flow graph and timeline."""

    project_id: int
    nodes: List[ContextFlowGraphNode]
    edges: List[ContextFlowGraphEdge]
    active_contexts_count: int
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ContextReportResponse(BaseModel):
    """Comprehensive context audit report."""

    project_id: int
    total_contexts: int
    valid_contexts: int
    invalid_contexts: int
    average_quality_score: float
    summary: Dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
