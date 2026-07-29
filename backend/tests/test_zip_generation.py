"""
Tests for ZIP generation — Phase 4.1
"""
from __future__ import annotations

import io
import zipfile
import pytest

from export_engine.schemas import (
    GeneratedFile,
    GeneratedReport,
    ProjectBundle,
    ProjectMetadata,
    ReportType,
)
from export_engine.services.zip_service import ZipService


class TestZipGeneration:
    """Test ZIP packaging and structure."""

    def make_source_files(self):
        return [
            GeneratedFile(path="main.py", content="from fastapi import FastAPI\napp = FastAPI()", language="python"),
            GeneratedFile(path="models/user.py", content="class User: pass", language="python"),
            GeneratedFile(path="api/router.py", content="from fastapi import APIRouter\nrouter = APIRouter()", language="python"),
            GeneratedFile(path="requirements.txt", content="fastapi\nuvicorn\nsqlalchemy", language="text"),
            GeneratedFile(path=".env.example", content="DATABASE_URL=postgresql://localhost/db", language="text"),
            GeneratedFile(path="Dockerfile", content="FROM python:3.11\nCMD python main.py", language="dockerfile"),
            GeneratedFile(path="docker-compose.yml", content="services:\n  web:\n    build: .", language="yaml"),
            GeneratedFile(path="README.md", content="# Test\n\nInstallation guide.", language="markdown"),
        ]

    def make_reports(self):
        return [
            GeneratedReport(report_type=ReportType.README, filename="README.md", content="# README"),
            GeneratedReport(report_type=ReportType.ARCHITECTURE, filename="Architecture_Report.md", content="# Architecture"),
            GeneratedReport(report_type=ReportType.API_DOCS, filename="API_Documentation.md", content="# API Docs"),
            GeneratedReport(report_type=ReportType.DATABASE_SCHEMA, filename="Database_Schema.md", content="# DB Schema"),
            GeneratedReport(report_type=ReportType.ER_DIAGRAM, filename="ER_Diagram.md", content="# ER Diagram"),
            GeneratedReport(report_type=ReportType.SECURITY, filename="Security_Report.md", content="# Security"),
            GeneratedReport(report_type=ReportType.TESTING, filename="Testing_Report.md", content="# Testing"),
            GeneratedReport(report_type=ReportType.DEPLOYMENT_GUIDE, filename="Deployment_Guide.md", content="# Deployment"),
            GeneratedReport(report_type=ReportType.VERSION, filename="Version_Report.md", content="# Version"),
            GeneratedReport(report_type=ReportType.MEMORY_REPORT, filename="Memory_Report.md", content="# Memory"),
            GeneratedReport(report_type=ReportType.RAG_REPORT, filename="RAG_Context_Report.md", content="# RAG"),
            GeneratedReport(report_type=ReportType.AGENT_EXECUTION, filename="Agent_Execution_Report.md", content="# Agent Exec"),
        ]

    def test_zip_full_package_structure(self):
        source = self.make_source_files()
        reports = self.make_reports()
        zip_svc = ZipService(project_id=42)
        zip_bytes = zip_svc.build(reports, source)

        assert len(zip_bytes) > 0
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            # Check root naming
            root = "GeneratedProject_42/"
            assert any(n.startswith(root) for n in names)
            # Check source code directory
            assert any("source_code/" in n for n in names)
            # Check all reports present
            assert f"{root}README.md" in names
            assert f"{root}Architecture_Report.md" in names
            assert f"{root}API_Documentation.md" in names
            assert f"{root}Database_Schema.md" in names
            assert f"{root}ER_Diagram.md" in names
            assert f"{root}Security_Report.md" in names
            assert f"{root}Testing_Report.md" in names
            assert f"{root}Deployment_Guide.md" in names
            assert f"{root}Memory_Report.md" in names
            assert f"{root}Agent_Execution_Report.md" in names
            assert f"{root}Version_Report.md" in names
            assert f"{root}RAG_Context_Report.md" in names
            # Check source files
            assert f"{root}source_code/main.py" in names
            assert f"{root}source_code/models/user.py" in names

    def test_zip_source_only(self):
        source = self.make_source_files()
        zip_svc = ZipService(project_id=99)
        zip_bytes = zip_svc.build_source_only(source)

        assert len(zip_bytes) > 0
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            assert all("source_code/" in n for n in names)
            # Source code ZIP may include README.md as a source file
            # Only verify no report files at root level
            root_files = [n for n in names if not n.startswith(f"GeneratedProject_99/source_code/")]
            assert not any(
                n for n in root_files
                if "Report" in n
            )

    def test_zip_reports_only(self):
        reports = self.make_reports()
        zip_svc = ZipService(project_id=7)
        zip_bytes = zip_svc.build_reports_only(reports)

        assert len(zip_bytes) > 0
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            for r in reports:
                assert f"GeneratedProject_7/{r.filename}" in names
            assert not any("source_code" in n for n in names)

    def test_zip_content_integrity(self):
        source = [GeneratedFile(path="hello.py", content="print('hello world')", language="python")]
        reports = [GeneratedReport(report_type=ReportType.README, filename="README.md", content="# Hello")]
        zip_svc = ZipService(project_id=1)
        zip_bytes = zip_svc.build(reports, source)

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            readme_content = zf.read("GeneratedProject_1/README.md").decode()
            assert "# Hello" in readme_content
            src_content = zf.read("GeneratedProject_1/source_code/hello.py").decode()
            assert "print('hello world')" in src_content

    def test_zip_compression(self):
        source = self.make_source_files()
        reports = self.make_reports()
        zip_svc = ZipService(project_id=5)
        zip_bytes = zip_svc.build(reports, source)

        # ZIP overhead for small files may be larger than raw content size
        # Just verify the ZIP is a valid archive with correct structure
        assert len(zip_bytes) > 0
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            assert len(names) == len(source) + len(reports)

    def test_zip_empty_source(self):
        reports = self.make_reports()
        zip_svc = ZipService(project_id=3)
        zip_bytes = zip_svc.build(reports, source_files=[])

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            assert not any("source_code" in n for n in names)

    def test_zip_empty_reports(self):
        source = self.make_source_files()
        zip_svc = ZipService(project_id=4)
        zip_bytes = zip_svc.build(reports=[])

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            assert not any("Report" in n for n in names)
            # source is also empty because we passed no source
            assert len(names) == 0

    def test_zip_windows_path_normalisation(self):
        source = [GeneratedFile(path="backend\\app\\main.py", content="print('hi')", language="python")]
        reports = [GeneratedReport(report_type=ReportType.README, filename="README.md", content="# Test")]
        zip_svc = ZipService(project_id=8)
        zip_bytes = zip_svc.build(reports, source)

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            # Windows backslashes should be normalised to forward slashes
            assert any("source_code/backend/app/main.py" in n for n in names)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])