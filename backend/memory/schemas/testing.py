"""
Testing memory schemas — Phase 5.1

Pydantic data contracts for the Testing Memory Engine.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TestingMemoryCreate(BaseModel):
    """Create a testing memory entry."""
    content: str = Field(..., min_length=1)
    agent_name: str = Field(default="qa_engineer")
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    test_type: Optional[str] = Field(default=None, description="unit/integration/e2e/performance/security")
    coverage_percent: Optional[float] = Field(default=None, ge=0, le=100, description="Code coverage %")
    pass_rate: Optional[float] = Field(default=None, ge=0, le=100, description="Test pass rate %")
    test_suite: Optional[str] = Field(default=None, description="Test suite name")
    test_framework: Optional[str] = Field(default=None, description="pytest/jest/mocha/cypress")
    total_tests: Optional[int] = Field(default=None, description="Total test count")
    failed_tests: Optional[int] = Field(default=None, description="Failed test count")
    skipped_tests: Optional[int] = Field(default=None, description="Skipped test count")


class TestingMemoryUpdate(BaseModel):
    """Update a testing memory entry."""
    content: str = Field(..., min_length=1)
    metadata_json: Optional[Dict[str, Any]] = None
    change_reason: str = Field(default="")
    changed_by: str = Field(default="system")
    test_type: Optional[str] = None
    coverage_percent: Optional[float] = None
    pass_rate: Optional[float] = None
    test_suite: Optional[str] = None
    test_framework: Optional[str] = None
    total_tests: Optional[int] = None
    failed_tests: Optional[int] = None
    skipped_tests: Optional[int] = None


class TestingMemoryResponse(BaseModel):
    """Response for a testing memory entry."""
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

    test_type: Optional[str] = None
    coverage_percent: Optional[float] = None
    pass_rate: Optional[float] = None
    test_suite: Optional[str] = None
    test_framework: Optional[str] = None
    total_tests: Optional[int] = None
    failed_tests: Optional[int] = None
    skipped_tests: Optional[int] = None

    model_config = {"from_attributes": True}


class TestingMemorySearchResult(BaseModel):
    """Search result for testing memory."""
    entries: List[TestingMemoryResponse]
    total: int
    query: str
