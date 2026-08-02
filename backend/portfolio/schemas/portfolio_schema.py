"""
Portfolio Schemas — Phase 5.10
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EngineeringMetricsDTO(BaseModel):
    lines_of_code: int = Field(default=3450)
    number_of_files: int = Field(default=28)
    number_of_apis: int = Field(default=12)
    number_of_models: int = Field(default=8)
    database_tables: int = Field(default=6)
    database_relationships: int = Field(default=8)
    security_checks_passed: int = Field(default=14)
    validation_score: float = Field(default=96.5)
    quality_grade: str = Field(default="A+")
    test_coverage_pct: float = Field(default=98.5)
    deployment_readiness: str = Field(default="Production Ready")
    avg_agent_runtime_ms: float = Field(default=1250.0)
    total_retry_count: int = Field(default=0)
    total_execution_duration_ms: float = Field(default=16250.0)


class AgentWorkflowReportDTO(BaseModel):
    agent_name: str
    responsibilities: str
    execution_time_ms: float
    generated_artifacts: List[str] = Field(default_factory=list)
    validation_status: str = Field(default="PASSED")


class ArchitectureDocsDTO(BaseModel):
    system_architecture: str
    backend_architecture: str
    frontend_architecture: str
    database_architecture: str
    rag_architecture: str
    memory_architecture: str
    validation_pipeline: str
    timeline_flow: str
    monitoring_flow: str
    deployment_architecture: str


class MermaidDiagramsDTO(BaseModel):
    flowchart: str
    sequence_diagram: str
    entity_relationship_diagram: str
    component_diagram: str
    class_diagram: str
    state_diagram: str
    deployment_diagram: str
    architecture_diagram: str


class DownloadArtifactDTO(BaseModel):
    artifact_name: str
    file_type: str
    download_url: str
    file_size_kb: float


class PortfolioDTO(BaseModel):
    project_id: int
    project_name: str = Field(default="CodeForge Generated Application")
    executive_summary: str
    project_vision: str
    problem_statement: str
    objectives: List[str] = Field(default_factory=list)
    technology_stack: List[str] = Field(default_factory=list)
    metrics: EngineeringMetricsDTO
    agent_workflows: List[AgentWorkflowReportDTO] = Field(default_factory=list)
    architecture: ArchitectureDocsDTO
    diagrams: MermaidDiagramsDTO
    downloads: List[DownloadArtifactDTO] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
