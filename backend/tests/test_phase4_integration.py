"""
Integration tests for Phase 4 modules — Export Engine, Validation Engine,
Testing Engine, and their interactions.
"""
from __future__ import annotations

import io
import zipfile
import pytest

from export_engine.schemas import (
    AgentOutputData,
    GeneratedFile,
    ProjectBundle,
    ProjectMetadata,
    ReportType,
)
from export_engine.services.export_service import ExportService
from export_engine.services.report_service import ReportService
from export_engine.services.zip_service import ZipService
from validation_engine.schemas import ProjectFiles, ValidationSeverity
from validation_engine.engine import ValidationEngine
from testing_engine.schemas import TestStatus
from testing_engine.engine import TestingEngine


class TestPhase4Integration:
    """Integration tests across Phase 4 modules."""

    def make_comprehensive_bundle(self) -> ProjectBundle:
        """Create a bundle that exercises all export, validation, and testing paths."""
        return ProjectBundle(
            metadata=ProjectMetadata(
                project_id=42,
                title="Integration Test Project",
                description="A comprehensive integration test",
                status="completed",
            ),
            agent_outputs=[
                AgentOutputData(agent_name="project_manager", status="completed", output_json={
                    "project_summary": "Integration test app",
                    "project_scope": "Full stack",
                    "goals": ["Goal 1", "Goal 2"],
                    "risks": [],
                }),
                AgentOutputData(agent_name="solution_architect", status="completed", output_json={
                    "file_structure": ["main.py", "models.py", "api/"],
                    "db_schema": [],
                    "endpoints": [],
                }),
                AgentOutputData(agent_name="database_engineer", status="completed", output_json={
                    "db_schema_details": "Tables: users, items",
                    "sqlalchemy_models_code": "class User(Base): pass",
                    "indexes": [],
                    "relationships": [],
                    "migration_plan": [],
                    "normalization_review": "OK",
                    "er_diagram_mermaid": "erDiagram USER ||--o{ ITEM",
                }),
                AgentOutputData(agent_name="api_designer", status="completed", output_json={
                    "authentication_flow": {"method": "JWT"},
                    "versioning_strategy": "URL prefix",
                    "endpoints": [],
                    "openapi_spec": "openapi: 3.1.0",
                }),
                AgentOutputData(agent_name="security_engineer", status="completed", output_json={
                    "overall_risk": "low",
                    "critical_count": 0, "high_count": 0, "medium_count": 0, "low_count": 0,
                    "findings": [],
                    "owasp_coverage": [],
                    "recommended_patches": [],
                }),
                AgentOutputData(agent_name="qa_engineer", status="completed", output_json={
                    "test_plan": "Test everything",
                    "estimated_coverage": 85.0,
                    "edge_cases": [],
                    "unit_tests_code": "",
                }),
                AgentOutputData(agent_name="devops_engineer", status="completed", output_json={
                    "deployment_guide": "Docker deploy",
                    "production_env_vars": [],
                    "dockerfile": "FROM python:3.11",
                    "docker_compose": "services:",
                }),
                AgentOutputData(agent_name="documentation_writer", status="completed", output_json={}),
            ],
            generated_files=[
                GeneratedFile(path="main.py", content="from fastapi import FastAPI\napp = FastAPI()\napp.include_router(router)", language="python"),
                GeneratedFile(path="models.py", content="class User: pass", language="python"),
                GeneratedFile(path="requirements.txt", content="fastapi\nuvicorn\nsqlalchemy", language="text"),
                GeneratedFile(path="Dockerfile", content="FROM python:3.11\nCMD python main.py", language="dockerfile"),
                GeneratedFile(path="docker-compose.yml", content="services:\n  web:\n    build: .", language="yaml"),
                GeneratedFile(path="README.md", content="# Test Project\n\n## Installation\n\npip install -r requirements.txt\n\n## Usage\n\nRun the app.", language="markdown"),
            ],
            memory_records=[],
            rag_context_used=[],
            version_history=[],
        )

    # === Export Engine Integration ===

    def test_export_engine_generates_all_reports(self):
        bundle = self.make_comprehensive_bundle()
        svc = ExportService()
        zip_bytes = svc.export_zip(bundle, include_source=True)

        assert len(zip_bytes) > 0
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            # Verify key reports exist
            assert any("README.md" in n for n in names)
            assert any("Architecture_Report.md" in n for n in names)
            assert any("API_Documentation.md" in n for n in names)
            assert any("Security_Report.md" in n for n in names)
            assert any("Testing_Report.md" in n for n in names)
            assert any("Deployment_Guide.md" in n for n in names)
            # Verify source code included
            assert any("source_code/main.py" in n for n in names)

    def test_export_engine_source_only(self):
        bundle = self.make_comprehensive_bundle()
        svc = ExportService()
        zip_bytes = svc.export_source_zip(bundle)

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            assert all("source_code/" in n for n in names)

    def test_export_engine_reports_only(self):
        bundle = self.make_comprehensive_bundle()
        svc = ExportService()
        zip_bytes = svc.export_reports_zip(bundle)

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            assert not any("source_code/" in n for n in names)
            assert any("README.md" in n for n in names)

    def test_export_describe_result(self):
        bundle = self.make_comprehensive_bundle()
        svc = ExportService()
        zip_bytes = svc.export_zip(bundle)
        result = svc.describe_export(bundle, zip_bytes)

        assert result.project_id == 42
        assert result.success is True
        assert result.zip_size_bytes > 0
        assert len(result.reports_generated) == 12

    # === Validation Engine Integration ===

    def test_validation_engine_full_validation(self):
        engine = ValidationEngine()
        files = ProjectFiles(
            files={
                "main.py": "from fastapi import FastAPI\napp = FastAPI()\napp.include_router(router)",
                "requirements.txt": "fastapi\nuvicorn\nsqlalchemy\n",
                "models.py": "from sqlalchemy import Column, Integer\nfrom sqlalchemy.orm import declarative_base\nBase = declarative_base()",
                "db.py": "from sqlalchemy.ext.asyncio import create_async_engine\nengine = create_async_engine('sqlite+aiosqlite:///test.db')",
                "auth.py": "from jose import jwt\nfrom passlib.context import CryptContext",
                "README.md": "# Test\n\n## Installation\n\npip install -r requirements.txt\n\n## Usage\n\nRun it.",
                "Dockerfile": "FROM python:3.11\nEXPOSE 8000\nCMD python main.py",
                "docker-compose.yml": "services:\n  web:\n    build: .",
            },
        )
        report = engine.validate(
            project_files=files,
            project_id=42,
            project_title="Validation Integration Test",
        )
        assert report.project_id == 42
        assert report.production_readiness_score >= 0
        assert len(report.categories) == 6

    def test_validation_engine_single_category(self):
        engine = ValidationEngine()
        files = ProjectFiles(files={"main.py": "from fastapi import FastAPI\napp = FastAPI()"})
        report = engine.validate(files, 42, "Test", categories=["fastapi"])
        assert len(report.categories) == 1
        assert report.categories[0].category == "fastapi"

    def test_validation_engine_from_bundle(self):
        engine = ValidationEngine()
        report = engine.validate_from_bundle(
            project_id=42,
            project_title="Bundle Test",
            generated_files=[
                {"path": "main.py", "content": "print('hi')"},
                {"path": "requirements.txt", "content": "fastapi"},
            ],
            agent_outputs={"project_manager": {}},
        )
        assert report.project_id == 42
        assert len(report.categories) == 6

    # === Testing Engine Integration ===

    def test_testing_engine_full_pipeline(self):
        engine = TestingEngine()
        files = [
            {"path": "main.py", "content": "from fastapi import FastAPI\napp = FastAPI()\napp.include_router(router)"},
            {"path": "requirements.txt", "content": "fastapi\nuvicorn\nsqlalchemy"},
            {"path": "models.py", "content": "class User: pass"},
            {"path": "db.py", "content": "from sqlalchemy.ext.asyncio import create_async_engine"},
            {"path": "auth.py", "content": "from jose import jwt\nfrom passlib.context import CryptContext\nBearer token"},
            {"path": "api/items.py", "content": "@router.get('/items')\ndef get(): pass\n@router.post('/items')\ndef post(): pass\n@router.put('/items/{id}')\ndef put(id): pass\n@router.delete('/items/{id}')\ndef delete(id): pass\nif item.owner_id == current_user.id: pass"},
            {"path": "README.md", "content": "# Test\n\n## Installation\n\npip install -r requirements.txt\n\n## Usage\n\nRun it.\n\n## Features\n\n- F1\n- F2\n- F3\n- F4\n- F5\n\n## API\n\nDoc.\n\n## License\n\nMIT."},
            {"path": "Dockerfile", "content": "FROM python:3.11\nEXPOSE 8000\nCMD python main.py"},
            {"path": "docker-compose.yml", "content": "services:\n  web:\n    build: ."},
        ]
        agent_outputs = {
            "devops_engineer": {
                "deployment_guide": "Deploy",
                "production_env_vars": [{"name": "DB_URL", "description": "DB", "is_secret": True}],
                "dockerfile": "FROM python:3.11",
                "docker_compose": "services:\n  web:\n    build: .",
            }
        }
        report = engine.run(
            project_id=42,
            project_title="Test Integration",
            generated_files=files,
            agent_outputs=agent_outputs,
        )
        assert report.project_id == 42
        assert len(report.results) == 15
        assert report.score >= 0
        assert report.score <= 100

    def test_testing_engine_specific_tests(self):
        engine = TestingEngine()
        files = [{"path": "main.py", "content": "print('hi')"}]
        report = engine.run(
            project_id=42,
            project_title="Test",
            generated_files=files,
            test_ids=["T01", "T03"],
        )
        assert len(report.results) == 2

    # === Cross-module Integration ===

    def test_export_validation_interop(self):
        """Verify export bundle can be consumed by validation engine."""
        bundle = self.make_comprehensive_bundle()
        files_dict = {f.path: f.content for f in bundle.generated_files}
        project_files = ProjectFiles(
            files=files_dict,
            agent_outputs={a.agent_name: a.output_json or {} for a in bundle.agent_outputs},
        )
        engine = ValidationEngine()
        report = engine.validate(project_files, 42, "Cross Test")
        assert report.production_readiness_score >= 0

    def test_export_testing_interop(self):
        """Verify export bundle can be consumed by testing engine."""
        bundle = self.make_comprehensive_bundle()
        files_list = [{"path": f.path, "content": f.content} for f in bundle.generated_files]
        agent_outputs = {a.agent_name: a.output_json or {} for a in bundle.agent_outputs}
        engine = TestingEngine()
        report = engine.run(42, "Cross Test", files_list, agent_outputs)
        assert len(report.results) == 15

    def test_zip_report_validation_roundtrip(self):
        """Generate ZIP, extract reports, validate content."""
        bundle = self.make_comprehensive_bundle()
        svc = ExportService()
        zip_bytes = svc.export_zip(bundle)

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            md_files = [n for n in names if n.endswith(".md")]
            assert len(md_files) >= 10
            for md in md_files:
                content = zf.read(md).decode()
                assert len(content) > 50, f"{md} has too little content"

    def test_full_phase4_pipeline(self):
        """Simulate the complete Phase 4 pipeline end-to-end."""
        # 1. Create project bundle from agent outputs
        bundle = self.make_comprehensive_bundle()

        # 2. Run validation engine
        val_engine = ValidationEngine()
        files_for_val = ProjectFiles(
            files={f.path: f.content for f in bundle.generated_files},
            agent_outputs={a.agent_name: a.output_json or {} for a in bundle.agent_outputs},
        )
        val_report = val_engine.validate(files_for_val, 42, "Pipeline Test")
        assert len(val_report.categories) == 6

        # 3. Run testing engine
        test_engine = TestingEngine()
        files_for_test = [{"path": f.path, "content": f.content} for f in bundle.generated_files]
        agent_outs = {a.agent_name: a.output_json or {} for a in bundle.agent_outputs}
        test_report = test_engine.run(42, "Pipeline Test", files_for_test, agent_outs)
        assert len(test_report.results) == 15

        # 4. Generate reports
        report_svc = ReportService()
        reports = report_svc.generate(bundle)
        assert len(reports) == 12

        # 5. Package into ZIP
        zip_svc = ZipService(42)
        zip_bytes = zip_svc.build(reports, bundle.generated_files)

        # 6. Verify ZIP is valid
        assert len(zip_bytes) > 0
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            assert len(zf.namelist()) > 15  # many files inside

        # 7. Verify export result metadata
        export_svc = ExportService()
        result = export_svc.describe_export(bundle, zip_bytes)
        assert result.success is True
        assert result.project_id == 42


if __name__ == "__main__":
    pytest.main([__file__, "-v"])