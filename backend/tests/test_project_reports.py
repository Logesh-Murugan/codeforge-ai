"""
Tests for Project Reports generation — Phase 4.5
"""
from __future__ import annotations

import pytest

from export_engine.schemas import (
    AgentOutputData,
    GeneratedFile,
    GeneratedReport,
    ProjectBundle,
    ProjectMetadata,
    ReportType,
)
from export_engine.services.report_service import ReportService
from export_engine.exporters.report_exporters import EXPORTER_REGISTRY


class TestProjectReports:
    """Test all project report types."""

    def make_full_bundle(self) -> ProjectBundle:
        """Create a comprehensive bundle for report testing."""
        return ProjectBundle(
            metadata=ProjectMetadata(
                project_id=1,
                title="Full Report Test",
                description="A comprehensive test project",
                status="completed",
            ),
            agent_outputs=[
                AgentOutputData(agent_name="project_manager", status="completed", output_json={
                    "project_summary": "Full stack app",
                    "project_scope": "Backend and frontend",
                    "goals": ["Goal 1", "Goal 2"],
                    "milestones": ["M1", "M2"],
                    "risks": ["Risk 1"],
                }),
                AgentOutputData(agent_name="solution_architect", status="completed", output_json={
                    "file_structure": ["main.py", "models.py", "api/"],
                    "db_schema": [{"table": "users", "columns": []}],
                    "endpoints": [{"method": "GET", "path": "/api/v1/items"}],
                }),
                AgentOutputData(agent_name="database_engineer", status="completed", output_json={
                    "db_schema_details": "Two tables with FK",
                    "sqlalchemy_models_code": "class User(Base): pass",
                    "indexes": [],
                    "relationships": [],
                    "migration_plan": ["Init migration"],
                    "normalization_review": "3NF",
                    "er_diagram_mermaid": "erDiagram USER ||--o{ ITEM",
                }),
                AgentOutputData(agent_name="api_designer", status="completed", output_json={
                    "authentication_flow": {"method": "JWT", "token_endpoint": "/auth/token"},
                    "versioning_strategy": "URL prefix",
                    "endpoints": [{"method": "GET", "path": "/items", "summary": "List items"}],
                    "request_models": [],
                    "openapi_spec": "openapi: 3.1.0",
                }),
                AgentOutputData(agent_name="security_engineer", status="completed", output_json={
                    "overall_risk": "low",
                    "critical_count": 0, "high_count": 0, "medium_count": 1, "low_count": 2,
                    "findings": [],
                    "owasp_coverage": ["A01"],
                }),
                AgentOutputData(agent_name="qa_engineer", status="completed", output_json={
                    "test_plan": "Full test plan",
                    "estimated_coverage": 90.0,
                    "edge_cases": [],
                    "unit_tests_code": "def test(): pass",
                }),
                AgentOutputData(agent_name="devops_engineer", status="completed", output_json={
                    "deployment_guide": "Deploy with Docker",
                    "production_env_vars": [],
                    "dockerfile": "FROM python:3.11",
                    "docker_compose": "services:",
                    "github_actions_workflow": "name: CI",
                    "nginx_config": "server { listen 80; }",
                }),
                AgentOutputData(agent_name="documentation_writer", status="completed", output_json={}),
            ],
            generated_files=[
                GeneratedFile(path="main.py", content="print('hi')", language="python"),
                GeneratedFile(path="models.py", content="class User: pass", language="python"),
            ],
            memory_records=[
                {"document": "mem1", "metadata": {"artifact_type": "requirements"}},
                {"document": "mem2", "metadata": {"artifact_type": "architecture"}},
            ],
            rag_context_used=[
                {"query": "Python patterns", "results": [{"document": "pat1", "similarity_score": 0.95}]},
            ],
            version_history=[
                {"version": 1, "agent_name": "pm", "artifact_type": "plan", "timestamp": "2024-01-01T00:00:00"},
            ],
        )

    def test_readme_report(self):
        bundle = self.make_full_bundle()
        svc = ReportService()
        reports = svc.generate(bundle, [ReportType.README])
        assert len(reports) == 1
        assert "Full Report Test" in reports[0].content
        assert "Goal 1" in reports[0].content

    def test_architecture_report(self):
        bundle = self.make_full_bundle()
        svc = ReportService()
        reports = svc.generate(bundle, [ReportType.ARCHITECTURE])
        assert len(reports) == 1
        assert "Architecture" in reports[0].content

    def test_api_docs_report(self):
        bundle = self.make_full_bundle()
        svc = ReportService()
        reports = svc.generate(bundle, [ReportType.API_DOCS])
        assert len(reports) == 1
        assert "API" in reports[0].content

    def test_database_schema_report(self):
        bundle = self.make_full_bundle()
        svc = ReportService()
        reports = svc.generate(bundle, [ReportType.DATABASE_SCHEMA])
        assert len(reports) == 1
        assert "Schema" in reports[0].content

    def test_er_diagram_report(self):
        bundle = self.make_full_bundle()
        svc = ReportService()
        reports = svc.generate(bundle, [ReportType.ER_DIAGRAM])
        assert len(reports) == 1
        assert "ER" in reports[0].content

    def test_security_report(self):
        bundle = self.make_full_bundle()
        svc = ReportService()
        reports = svc.generate(bundle, [ReportType.SECURITY])
        assert len(reports) == 1
        assert "Security" in reports[0].content
        assert "Risk" in reports[0].content

    def test_testing_report(self):
        bundle = self.make_full_bundle()
        svc = ReportService()
        reports = svc.generate(bundle, [ReportType.TESTING])
        assert len(reports) == 1
        assert "Testing" in reports[0].content
        assert "Coverage" in reports[0].content

    def test_deployment_guide_report(self):
        bundle = self.make_full_bundle()
        svc = ReportService()
        reports = svc.generate(bundle, [ReportType.DEPLOYMENT_GUIDE])
        assert len(reports) == 1
        assert "Deployment" in reports[0].content

    def test_agent_execution_report(self):
        bundle = self.make_full_bundle()
        svc = ReportService()
        reports = svc.generate(bundle, [ReportType.AGENT_EXECUTION])
        assert len(reports) == 1
        assert "Agent Execution" in reports[0].content
        assert "Project Manager" in reports[0].content

    def test_version_report(self):
        bundle = self.make_full_bundle()
        svc = ReportService()
        reports = svc.generate(bundle, [ReportType.VERSION])
        assert len(reports) == 1
        assert "Version" in reports[0].content

    def test_memory_report(self):
        bundle = self.make_full_bundle()
        svc = ReportService()
        reports = svc.generate(bundle, [ReportType.MEMORY_REPORT])
        assert len(reports) == 1
        assert "Memory" in reports[0].content

    def test_rag_report(self):
        bundle = self.make_full_bundle()
        svc = ReportService()
        reports = svc.generate(bundle, [ReportType.RAG_REPORT])
        assert len(reports) == 1
        assert "RAG" in reports[0].content

    def test_all_reports_distinct_filenames(self):
        bundle = self.make_full_bundle()
        svc = ReportService()
        reports = svc.generate(bundle)
        filenames = [r.filename for r in reports]
        assert len(set(filenames)) == len(filenames), "Duplicate filenames found"

    def test_all_reports_have_content(self):
        bundle = self.make_full_bundle()
        svc = ReportService()
        reports = svc.generate(bundle)
        for r in reports:
            assert len(r.content) > 50, f"Report {r.filename} has too little content"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])