"""
Security memory schemas — Phase 5.1

Pydantic data contracts for the Security Memory Engine.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SecurityMemoryCreate(BaseModel):
    """Create a security memory entry."""
    content: str = Field(..., min_length=1)
    agent_name: str = Field(default="security_engineer")
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    severity: Optional[str] = Field(default=None, description="Severity: critical/high/medium/low/info")
    vulnerability_type: Optional[str] = Field(default=None, description="Vulnerability classification")
    remediation: Optional[str] = Field(default=None, description="Remediation steps")
    scan_type: Optional[str] = Field(default=None, description="sast/dast/dependency/manual")
    affected_component: Optional[str] = Field(default=None, description="Affected component or file")
    cwe_id: Optional[str] = Field(default=None, description="CWE identifier")
    compliance: Optional[List[str]] = Field(default=None, description="Compliance frameworks: owasp/pci/gdpr")


class SecurityMemoryUpdate(BaseModel):
    """Update a security memory entry."""
    content: str = Field(..., min_length=1)
    metadata_json: Optional[Dict[str, Any]] = None
    change_reason: str = Field(default="")
    changed_by: str = Field(default="system")
    severity: Optional[str] = None
    vulnerability_type: Optional[str] = None
    remediation: Optional[str] = None
    scan_type: Optional[str] = None
    affected_component: Optional[str] = None
    cwe_id: Optional[str] = None
    compliance: Optional[List[str]] = None


class SecurityMemoryResponse(BaseModel):
    """Response for a security memory entry."""
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

    severity: Optional[str] = None
    vulnerability_type: Optional[str] = None
    remediation: Optional[str] = None
    scan_type: Optional[str] = None
    affected_component: Optional[str] = None
    cwe_id: Optional[str] = None
    compliance: Optional[List[str]] = None

    model_config = {"from_attributes": True}


class SecurityMemorySearchResult(BaseModel):
    """Search result for security memory."""
    entries: List[SecurityMemoryResponse]
    total: int
    query: str
