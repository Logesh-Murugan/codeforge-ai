"""
Export Engine Pydantic schemas — Phase 4.1
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class ExportFormat(str, Enum):
    """Supported export output formats."""
    ZIP          = "zip"
    MARKDOWN     = "markdown"
    JSON         = "json"
    HTML         = "html"


class ReportType(str, Enum):
    """Individual report types the engine can produce."""
    README               = "readme"
    ARCHITECTURE         = "architecture"
    API_DOCS             = "api_docs"
    DATABASE_SCHEMA      = "database_schema"
    ER_DIAGRAM           = "er_diagram"
    AGENT_EXECUTION      = "agent_execution"
    SECURITY             = "security"
    TESTING              = "testing"
    VERSION              = "version"
    DEPLOYMENT_GUIDE     = "deployment_guide"
    MEMORY_REPORT        = "memory_report"
    RAG_REPORT           = "rag_report"
    FULL_PROJECT         = "full_project"


# ---------------------------------------------------------------------------
# Input schemas
# ---------------------------------------------------------------------------

class AgentOutputData(BaseModel):
    """Agent output data passed to the export engine."""
    agent_name: str
    status: str = "completed"
    output_json: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time_seconds: Optional[float] = None
    retry_count: int = 0
    generated_files: List[Dict[str, str]] = Field(default_factory=list)
    memory_records_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class GeneratedFile(BaseModel):
    """A single generated source file."""
    path: str
    content: str
    language: str = "text"


class ProjectMetadata(BaseModel):
    """Metadata for the project being exported."""
    project_id: int
    title: str
    description: Optional[str] = None
    status: str = "completed"
    owner: Optional[str] = None
    created_at: Optional[str] = None


class ProjectBundle(BaseModel):
    """
    Complete data bundle fed into the export engine.
    Collected from DB agent runs, memory system, and project record.
    """
    metadata: ProjectMetadata
    agent_outputs: List[AgentOutputData] = Field(default_factory=list)
    generated_files: List[GeneratedFile] = Field(default_factory=list)
    memory_records: List[Dict[str, Any]] = Field(default_factory=list)
    rag_context_used: List[Dict[str, Any]] = Field(default_factory=list)
    version_history: List[Dict[str, Any]] = Field(default_factory=list)

    def get_agent(self, name: str) -> Optional[AgentOutputData]:
        """Return agent output by name, or None."""
        for a in self.agent_outputs:
            if a.agent_name == name:
                return a
        return None

    def get_agent_output_json(self, name: str) -> Dict[str, Any]:
        """Return the output_json dict for an agent, or empty dict."""
        a = self.get_agent(name)
        if a and a.output_json:
            return a.output_json
        return {}


# ---------------------------------------------------------------------------
# Output schemas
# ---------------------------------------------------------------------------

class ReportSection(BaseModel):
    """A single named section within a generated report."""
    title: str
    content: str
    level: int = 2   # markdown heading level


class GeneratedReport(BaseModel):
    """A single fully-rendered report document."""
    report_type: ReportType
    filename: str
    content: str
    format: ExportFormat = ExportFormat.MARKDOWN
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class ExportRequest(BaseModel):
    """Request to the export service."""
    project_id: int
    report_types: List[ReportType] = Field(
        default_factory=lambda: list(ReportType)
    )
    include_source_code: bool = True
    export_format: ExportFormat = ExportFormat.ZIP


class ExportResult(BaseModel):
    """Result returned by the export service."""
    project_id: int
    reports_generated: List[str]
    total_files: int
    zip_size_bytes: int = 0
    success: bool = True
    errors: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
