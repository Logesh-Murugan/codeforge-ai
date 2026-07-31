"""
Context Payload Schemas — Phase 5.5

Defines the 21 Context Types and Pydantic models for context entities.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ContextType(str, Enum):
    PROJECT = "Project"
    REQUIREMENT = "Requirement"
    ARCHITECTURE = "Architecture"
    MEMORY = "Memory"
    RAG = "RAG"
    HUMAN_APPROVAL = "Human Approval"
    AGENT = "Agent"
    WORKFLOW = "Workflow"
    TIMELINE = "Timeline"
    VALIDATION = "Validation"
    SECURITY = "Security"
    TESTING = "Testing"
    DOCUMENTATION = "Documentation"
    DEPLOYMENT = "Deployment"
    EXPORT = "Export"
    GENERATED_FILES = "Generated Files"
    FRONTEND = "Frontend"
    BACKEND = "Backend"
    DATABASE = "Database"
    API = "API"
    COLLABORATION = "Collaboration"


class ContextCreateRequest(BaseModel):
    """Payload to register or update a context item."""

    project_id: int = Field(..., description="Owning project ID.")
    context_type: ContextType = Field(..., description="One of the 21 supported context types.")
    producer_agent: str = Field(default="system", description="Agent/system generating the context.")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Context content payload.")


class ContextEntityResponse(BaseModel):
    """Details of a registered context entity."""

    id: int
    project_id: int
    context_type: str
    version: int
    producer_agent: str
    payload: Dict[str, Any]
    status: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ContextBundleRequest(BaseModel):
    """Request payload to retrieve routed context bundle for a target agent."""

    project_id: int
    target_agent: str = Field(..., description="Target agent name (e.g. backend_developer).")
    required_context_types: Optional[List[ContextType]] = None
