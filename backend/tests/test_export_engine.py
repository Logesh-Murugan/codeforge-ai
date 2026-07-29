"""
Tests for Export Engine — Phase 4.1
"""
from __future__ import annotations

import pytest

from export_engine.schemas import (
    AgentOutputData,
    ExportFormat,
    GeneratedFile,
    GeneratedReport,
    ProjectBundle,
    ProjectMetadata,
    ReportType,
)
from export_engine.services.export_service import ExportService
from export_engine.services.report_service import ReportService
from export_engine.services.zip_service import ZipService
from export_engine.exporters.report_exporters import EXPORTER_REGISTRY


class TestExportSchemas:
    """Test export engine schemas."""

    def test_project_metadata(self):
        meta = ProjectMetadata(
            project_id=1,
            title="Test Project",
            description="A test project",
            status="completed",
        )
        assert meta.project_id == 1
        assert meta.title == "Test Project"

    def test_agent_output_data(self):
        agent = AgentOutputData(
            agent_name="project_manager",
            status="completed",
            output_json={"goals": ["goal1"]},
            execution_time_seconds=1.5,
            retry_count=0,
        )
        assert agent.agent_name == "project_manager"
        assert agent.status == "completed"

    def test_generated_file(self):
        f = GeneratedFile(path="main.py", content="print('hi')", language="python")
        assert f.path == "main.py"
        assert f.language == "python"

    def test_project_bundle_get_agent(self):
        bundle = ProjectBundle(
            metadata=ProjectMetadata(project_id=1, title="Test"),
            agent_outputs=[
                AgentOutputData(agent_name="pm", status="completed", output_json={"key": "val"}),
            ],
        )
        agent = bundle.get_agent("pm")
        assert agent is not None
        assert agent.agent_name == "pm"

        missing = bundle.get_agent("missing")
        assert missing is None

    def test_project_bundle_get_agent_output_json(self):
        bundle = ProjectBundle(
            metadata=ProjectMetadata(project_id=1, title="Test"),
            agent_outputs=[
                AgentOutputData(agent_name="pm", output_json={"goals": ["g1"]}),
            ],
        )
        out = bundle.get_agent_output_json("pm")
        assert out == {"goals": ["g1"]}

        empty = bundle.get_agent_output_json("missing")
        assert empty == {}

    def test_report_type_enum(self):
        assert ReportType.README == "readme"
        assert ReportType.ARCHITECTURE == "architecture"
        assert ReportType.SECURITY == "security"
        assert len(list(ReportType)) == 13  # 12 reports + FULL_PROJECT

    def test_export_format_enum(self):
        assert ExportFormat.ZIP == "zip"
        assert ExportFormat.MARKDOWN == "markdown"
        assert ExportFormat.JSON == "json"
        assert ExportFormat.HTML == "html"


class TestReportExporters:
    """Test individual report exporters."""

    def make_bundle(self) -> ProjectBundle:
        """Create a minimal valid ProjectBundle for testing."""
        return ProjectBundle(
            metadata=ProjectMetadata(
                project_id=1,
                title="Test Project",
                description="A test project description",
                status="completed",
            ),
            agent_outputs=[
                AgentOutputData(
                    agent_name="project_manager",
                    status="completed",
                    output_json={
                        "project_summary": "Summary",
                        "project_scope": "Scope",
                        "goals": ["Goal 1", "Goal 2"],
                        "risks": ["Risk 1"],
                        "agent_execution_plan": [
                            {"agent": "pm", "input_from": "user", "description": "Plan"}
                        ],
                    },
                ),
                AgentOutputData(
                    agent_name="solution_architect",
                    status="completed",
                    output_json={
                        "file_structure": ["main.py", "models.py"],
                        "db_schema": [{"table": "users", "columns": [{"name": "id", "type": "int", "is_fk": False}]}],
                        "endpoints": [
                            {"method": "GET", "path": "/items", "description": "List items", "requires_auth": True}
                        ],
                    },
                ),
                AgentOutputData(
                    agent_name="database_engineer",
                    status="completed",
                    output_json={
                        "db_schema_details": "Schema details",
                        "sqlalchemy_models_code": "class User: pass",
                        "indexes": [{"name": "ix_user_email", "table": "users", "columns": ["email"], "unique": True}],
                        "relationships": [{"name": "user_items", "from_table": "users", "to_table": "items", "cardinality": "1:N"}],
                        "migration_plan": ["CREATE TABLE users..."],
                        "normalization_review": "3NF compliant",
                        "er_diagram_mermaid": "erDiagram\n  USER ||--o{ ITEM",
                    },
                ),
                AgentOutputData(
                    agent_name="api_designer",
                    status="completed",
                    output_json={
                        "authentication_flow": {"method": "JWT", "token_endpoint": "/token", "refresh_endpoint": "/refresh", "description": "JWT flow"},
                        "versioning_strategy": "URL path",
                        "endpoints": [
                            {"method": "GET", "path": "/items", "summary": "List items", "auth_required": True, "request_model": "ItemCreate", "response_model": "ItemList", "error_responses": ["401", "404"]},
                        ],
                        "request_models": [{"name": "ItemCreate", "fields": [{"name": "name", "type": "str", "description": "Item name"}]}],
                        "openapi_spec": "openapi: 3.1.0\ninfo:\n  title: Test",
                    },
                ),
                AgentOutputData(
                    agent_name="security_engineer",
                    status="completed",
                    output_json={
                        "overall_risk": "low",
                        "critical_count": 0,
                        "high_count": 0,
                        "medium_count": 1,
                        "low_count": 2,
                        "jwt_assessment": "JWT properly configured",
                        "findings": [
                            {"severity": "medium", "category": "Auth", "title": "Weak secret", "description": "Use stronger secret", "recommendation": "Rotate secret", "file": "auth.py", "line": 10, "code_snippet": "SECRET = 'weak'"},
                        ],
                        "owasp_coverage": ["A01", "A02"],
                        "recommended_patches": ["Update secret"],
                    },
                ),
                AgentOutputData(
                    agent_name="qa_engineer",
                    status="completed",
                    output_json={
                        "test_plan": "Test all endpoints",
                        "estimated_coverage": 85.0,
                        "coverage_report_summary": "Good coverage",
                        "edge_cases": [{"name": "Empty list", "type": "boundary", "description": "Handle empty"}],
                        "unit_tests_code": "def test_get(): pass",
                    },
                ),
                AgentOutputData(
                    agent_name="devops_engineer",
                    status="completed",
                    output_json={
                        "deployment_guide": "Deploy to cloud",
                        "production_env_vars": [{"name": "DB_URL", "description": "Database URL", "default_value": "", "is_secret": True}],
                        "dockerfile": "FROM python:3.11\nCMD python main.py",
                        "docker_compose": "services:\n  web:\n    build: .",
                        "github_actions_workflow": "name: CI\non: push\njobs:\n  test:\n    runs-on: ubuntu-latest",
                        "nginx_config": "server { listen 80; }",
                    },
                ),
                AgentOutputData(
                    agent_name="documentation_writer",
                    status="completed",
                    output_json={},
                ),
            ],
            generated_files=[
                GeneratedFile(path="main.py", content="from fastapi import FastAPI\napp = FastAPI()", language="python"),
                GeneratedFile(path="models.py", content="class User: pass", language="python"),
                GeneratedFile(path="requirements.txt", content="fastapi\nuvicorn", language="text"),
            ],
            memory_records=[
                {"document": "req1", "metadata": {"artifact_type": "requirements"}},
                {"document": "arch1", "metadata": {"artifact_type": "architecture"}},
            ],
            rag_context_used=[
                {"query": "FastAPI patterns", "results": [{"document": "pattern1", "similarity_score": 0.9}]},
            ],
            version_history=[
                {"version": 1, "agent_name": "pm", "artifact_type": "plan", "timestamp": "2024-01-01T00:00:00"},
            ],
        )

    def test_export_readme(self):
        bundle = self.make_bundle()
        from export_engine.exporters.report_exporters import export_readme

        report = export_readme(bundle)
        assert report.report_type == ReportType.README
        assert report.filename == "README.md"
        assert "Test Project" in report.content
        assert "Goal 1" in report.content

    def test_export_architecture(self):
        bundle = self.make_bundle()
        from export_engine.exporters.report_exporters import export_architecture

        report = export_architecture(bundle)
        assert report.report_type == ReportType.ARCHITECTURE
        assert "File Structure" in report.content
        assert "Database Schema" in report.content

    def test_export_api_docs(self):
        bundle = self.make_bundle()
        from export_engine.exporters.report_exporters import export_api_docs

        report = export_api_docs(bundle)
        assert report.report_type == ReportType.API_DOCS
        assert "Authentication" in report.content
        assert "Endpoints" in report.content

    def test_export_database_schema(self):
        bundle = self.make_bundle()
        from export_engine.exporters.report_exporters import export_database_schema

        report = export_database_schema(bundle)
        assert report.report_type == ReportType.DATABASE_SCHEMA
        assert "SQLAlchemy Models" in report.content

    def test_export_er_diagram(self):
        bundle = self.make_bundle()
        from export_engine.exporters.report_exporters import export_er_diagram

        report = export_er_diagram(bundle)
        assert report.report_type == ReportType.ER_DIAGRAM
        assert "ER Diagram" in report.content or "Entity" in report.content

    def test_export_agent_execution(self):
        bundle = self.make_bundle()
        from export_engine.exporters.report_exporters import export_agent_execution

        report = export_agent_execution(bundle)
        assert report.report_type == ReportType.AGENT_EXECUTION
        assert "Agent Execution Report" in report.content
        assert "Project Manager" in report.content

    def test_export_security(self):
        bundle = self.make_bundle()
        from export_engine.exporters.report_exporters import export_security

        report = export_security(bundle)
        assert report.report_type == ReportType.SECURITY
        assert "Overall Risk" in report.content
        assert "Findings" in report.content

    def test_export_testing(self):
        bundle = self.make_bundle()
        from export_engine.exporters.report_exporters import export_testing

        report = export_testing(bundle)
        assert report.report_type == ReportType.TESTING
        assert "Test Plan" in report.content
        assert "Coverage" in report.content

    def test_export_deployment_guide(self):
        bundle = self.make_bundle()
        from export_engine.exporters.report_exporters import export_deployment_guide

        report = export_deployment_guide(bundle)
        assert report.report_type == ReportType.DEPLOYMENT_GUIDE
        assert "Deployment" in report.content
        assert "Dockerfile" in report.content

    def test_export_version(self):
        bundle = self.make_bundle()
        from export_engine.exporters.report_exporters import export_version

        report = export_version(bundle)
        assert report.report_type == ReportType.VERSION
        assert "Version Report" in report.content
        assert "Generated Files" in report.content

    def test_export_memory_report(self):
        bundle = self.make_bundle()
        from export_engine.exporters.report_exporters import export_memory_report

        report = export_memory_report(bundle)
        assert report.report_type == ReportType.MEMORY_REPORT
        assert "Memory Report" in report.content

    def test_export_rag_report(self):
        bundle = self.make_bundle()
        from export_engine.exporters.report_exporters import export_rag_report

        report = export_rag_report(bundle)
        assert report.report_type == ReportType.RAG_REPORT
        assert "RAG Context" in report.content


class TestReportService:
    """Test ReportService orchestration."""

    def make_bundle(self) -> ProjectBundle:
        """Create a minimal valid ProjectBundle for testing."""
        return ProjectBundle(
            metadata=ProjectMetadata(project_id=1, title="Test Project"),
            agent_outputs=[
                AgentOutputData(agent_name="project_manager", status="completed"),
                AgentOutputData(agent_name="security_engineer", status="completed"),
            ],
        )

    def test_generate_all_reports(self):
        bundle = self.make_bundle()
        svc = ReportService()
        reports = svc.generate(bundle)

        assert len(reports) == 12  # All except FULL_PROJECT
        types = {r.report_type for r in reports}
        assert ReportType.FULL_PROJECT not in types

    def test_generate_specific_reports(self):
        bundle = self.make_bundle()
        svc = ReportService()
        reports = svc.generate(bundle, [ReportType.README, ReportType.SECURITY])

        assert len(reports) == 2
        types = {r.report_type for r in reports}
        assert types == {ReportType.README, ReportType.SECURITY}


class TestZipService:
    """Test ZipService packaging."""

    def make_bundle(self) -> ProjectBundle:
        """Create a minimal valid ProjectBundle for testing."""
        return ProjectBundle(
            metadata=ProjectMetadata(project_id=1, title="Test Project"),
            agent_outputs=[
                AgentOutputData(agent_name="project_manager", status="completed"),
                AgentOutputData(agent_name="security_engineer", status="completed"),
            ],
            generated_files=[
                GeneratedFile(path="main.py", content="print('hi')", language="python"),
            ],
        )

    def test_build_zip_with_reports_and_source(self):
        bundle = self.make_bundle()
        svc = ReportService()
        reports = svc.generate(bundle)

        zip_svc = ZipService(1)
        zip_bytes = zip_svc.build(reports, bundle.generated_files)

        assert len(zip_bytes) > 0
        # Verify it's a valid ZIP
        import zipfile
        import io
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            assert any("README.md" in n for n in names)
            assert any("source_code/main.py" in n for n in names)

    def test_build_source_only(self):
        bundle = self.make_bundle()
        zip_svc = ZipService(1)
        zip_bytes = zip_svc.build_source_only(bundle.generated_files)

        assert len(zip_bytes) > 0
        import zipfile
        import io
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            assert any("source_code/main.py" in n for n in names)
            assert not any("README.md" in n for n in names)

    def test_build_reports_only(self):
        bundle = self.make_bundle()
        svc = ReportService()
        reports = svc.generate(bundle)

        zip_svc = ZipService(1)
        zip_bytes = zip_svc.build_reports_only(reports)

        assert len(zip_bytes) > 0
        import zipfile
        import io
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            assert any("README.md" in n for n in names)
            assert not any("source_code/" in n for n in names)


class TestExportService:
    """Test ExportService end-to-end."""

    def make_bundle(self) -> ProjectBundle:
        """Create a minimal valid ProjectBundle for testing."""
        return ProjectBundle(
            metadata=ProjectMetadata(project_id=1, title="Test Project"),
            agent_outputs=[
                AgentOutputData(agent_name="project_manager", status="completed"),
                AgentOutputData(agent_name="security_engineer", status="completed"),
            ],
            generated_files=[
                GeneratedFile(path="main.py", content="print('hi')", language="python"),
            ],
        )

    def test_build_bundle(self):
        svc = ExportService()
        bundle = svc.build_bundle(
            project_id=1,
            project_title="Test",
            project_description="Desc",
            project_status="completed",
            agent_runs_raw=[
                {"agent_name": "pm", "status": "completed", "output_json": {"goals": ["g1"]}},
            ],
            generated_files_raw=[{"path": "main.py", "content": "print('hi')"}],
        )
        assert bundle.metadata.project_id == 1
        assert len(bundle.agent_outputs) == 1
        assert len(bundle.generated_files) == 1

    def test_export_zip(self):
        bundle = self.make_bundle()
        svc = ExportService()
        zip_bytes = svc.export_zip(bundle)

        assert len(zip_bytes) > 0
        import zipfile
        import io
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            assert len(zf.namelist()) > 10  # Reports + source files

    def test_export_source_zip(self):
        bundle = self.make_bundle()
        svc = ExportService()
        zip_bytes = svc.export_source_zip(bundle)

        assert len(zip_bytes) > 0
        import zipfile
        import io
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            assert any("source_code/main.py" in n for n in names)

    def test_export_reports_zip(self):
        bundle = self.make_bundle()
        svc = ExportService()
        zip_bytes = svc.export_reports_zip(bundle)

        assert len(zip_bytes) > 0
        import zipfile
        import io
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            assert any("README.md" in n for n in names)
            assert not any("source_code/" in n for n in names)

    def test_describe_export(self):
        bundle = self.make_bundle()
        svc = ExportService()
        zip_bytes = svc.export_zip(bundle)
        result = svc.describe_export(bundle, zip_bytes)

        assert result.project_id == 1
        assert result.success is True
        assert result.zip_size_bytes == len(zip_bytes)
        assert len(result.reports_generated) == 12


class TestExporterRegistry:
    """Test that all exporters are registered."""

    def test_all_report_types_registered(self):
        expected = {
            ReportType.README,
            ReportType.ARCHITECTURE,
            ReportType.API_DOCS,
            ReportType.DATABASE_SCHEMA,
            ReportType.ER_DIAGRAM,
            ReportType.AGENT_EXECUTION,
            ReportType.SECURITY,
            ReportType.TESTING,
            ReportType.DEPLOYMENT_GUIDE,
            ReportType.VERSION,
            ReportType.MEMORY_REPORT,
            ReportType.RAG_REPORT,
        }
        actual = set(EXPORTER_REGISTRY.keys())
        # FULL_PROJECT is not in registry
        assert expected.issubset(actual)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])