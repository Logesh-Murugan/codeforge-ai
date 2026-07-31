"""
Deployment memory schemas — Phase 5.1

Pydantic data contracts for the Deployment Memory Engine.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DeploymentMemoryCreate(BaseModel):
    """Create a deployment memory entry."""
    content: str = Field(..., min_length=1)
    agent_name: str = Field(default="devops_engineer")
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    environment: Optional[str] = Field(default=None, description="dev/staging/production")
    provider: Optional[str] = Field(default=None, description="Cloud provider: render/vercel/aws/gcp")
    config_type: Optional[str] = Field(default=None, description="dockerfile/compose/k8s/ci-cd/terraform")
    status: Optional[str] = Field(default=None, description="pending/deployed/failed/rolled-back")
    deploy_url: Optional[str] = Field(default=None, description="Deployment URL")
    build_command: Optional[str] = Field(default=None, description="Build command")
    env_variables: Optional[List[str]] = Field(default=None, description="Required env variable names")
    health_check_url: Optional[str] = Field(default=None, description="Health check endpoint")


class DeploymentMemoryUpdate(BaseModel):
    """Update a deployment memory entry."""
    content: str = Field(..., min_length=1)
    metadata_json: Optional[Dict[str, Any]] = None
    change_reason: str = Field(default="")
    changed_by: str = Field(default="system")
    environment: Optional[str] = None
    provider: Optional[str] = None
    config_type: Optional[str] = None
    status: Optional[str] = None
    deploy_url: Optional[str] = None
    build_command: Optional[str] = None
    env_variables: Optional[List[str]] = None
    health_check_url: Optional[str] = None


class DeploymentMemoryResponse(BaseModel):
    """Response for a deployment memory entry."""
    id: int
    project_id: int
    category: str
    agent_name: str
    content: str
    metadata_json: Dict[str, Any]
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    environment: Optional[str] = None
    provider: Optional[str] = None
    config_type: Optional[str] = None
    status: Optional[str] = None
    deploy_url: Optional[str] = None
    build_command: Optional[str] = None
    env_variables: Optional[List[str]] = None
    health_check_url: Optional[str] = None

    model_config = {"from_attributes": True}


class DeploymentMemorySearchResult(BaseModel):
    """Search result for deployment memory."""
    entries: List[DeploymentMemoryResponse]
    total: int
    query: str
