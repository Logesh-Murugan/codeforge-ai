"""
Tests for Validation Engine — Phase 4.2
"""
from __future__ import annotations

import pytest

from validation_engine.schemas import (
    ValidationSeverity,
    ValidationStatus,
    ValidationIssue,
    CategoryResult,
    ValidationReport,
    ValidationRequest,
    ProjectFiles,
)
from validation_engine.engine import ValidationEngine
from validation_engine.validators import VALIDATOR_REGISTRY


class TestValidationSchemas:
    """Test validation engine schemas."""

    def test_validation_severity_enum(self):
        assert ValidationSeverity.ERROR == "error"
        assert ValidationSeverity.WARNING == "warning"
        assert ValidationSeverity.INFO == "info"

    def test_validation_status_enum(self):
        assert ValidationStatus.PASS == "pass"
        assert ValidationStatus.FAIL == "fail"
        assert ValidationStatus.SKIPPED == "skipped"

    def test_validation_issue(self):
        issue = ValidationIssue(
            category="test",
            severity=ValidationSeverity.ERROR,
            code="TEST_CODE",
            message="Test message",
            file="test.py",
            recommendation="Fix it",
        )
        assert issue.category == "test"
        assert issue.severity == ValidationSeverity.ERROR

    def test_category_result(self):
        issues = [
            ValidationIssue(
                category="test",
                severity=ValidationSeverity.ERROR,
                code="ERR1",
                message="Error",
            ),
            ValidationIssue(
                category="test",
                severity=ValidationSeverity.WARNING,
                code="WARN1",
                message="Warning",
            ),
        ]
        result = CategoryResult(
            category="test",
            status=ValidationStatus.FAIL,
            score=50,
            issues=issues,
            checks_run=10,
            checks_passed=5,
        )
        assert result.error_count == 1
        assert result.warning_count == 1

    def test_validation_report_compute(self):
        cat1 = CategoryResult(
            category="cat1",
            status=ValidationStatus.PASS,
            score=100,
            issues=[],
            checks_run=5,
            checks_passed=5,
        )
        cat2 = CategoryResult(
            category="cat2",
            status=ValidationStatus.FAIL,
            score=50,
            issues=[
                ValidationIssue(
                    category="cat2",
                    severity=ValidationSeverity.ERROR,
                    code="ERR",
                    message="Error",
                )
            ],
            checks_run=4,
            checks_passed=2,
        )
        report = ValidationReport.compute(1, "Test Project", [cat1, cat2])
        assert report.project_id == 1
        assert report.project_title == "Test Project"
        assert report.overall_status == ValidationStatus.FAIL
        assert report.total_errors == 1
        assert report.total_warnings == 0

    def test_project_files_find(self):
        files = ProjectFiles(
            files={
                "main.py": "content",
                "models.py": "models",
                "auth.py": "auth",
            }
        )
        assert files.find("main") == ["main.py"]
        assert files.find("model") == ["models.py"]
        assert files.find("auth") == ["auth.py"]
        assert files.find("missing") == []

    def test_validation_request(self):
        req = ValidationRequest(project_id=1, categories=["source_code", "fastapi"])
        assert req.project_id == 1
        assert req.categories == ["source_code", "fastapi"]


class TestValidators:
    """Test individual validators."""

    def test_source_code_validator(self):
        from validation_engine.validators import validate_source_code

        files = ProjectFiles(
            files={
                "main.py": "from fastapi import FastAPI\napp = FastAPI()",
                "requirements.txt": "fastapi\nuvicorn\nsqlalchemy\n",
            }
        )
        result = validate_source_code(files)
        assert result.category == "source_code"
        assert result.status in (ValidationStatus.PASS, ValidationStatus.FAIL)
        assert result.checks_run > 0

    def test_fastapi_validator(self):
        from validation_engine.validators import validate_fastapi

        files = ProjectFiles(
            files={
                "main.py": "from fastapi import FastAPI\napp = FastAPI()\napp.include_router(router)",
                "api/router.py": "from fastapi import APIRouter\nrouter = APIRouter()\n@router.get('/')\ndef root(): pass",
            }
        )
        result = validate_fastapi(files)
        assert result.category == "fastapi"
        assert result.checks_run > 0

    def test_database_validator(self):
        from validation_engine.validators import validate_database

        files = ProjectFiles(
            files={
                "models.py": "from sqlalchemy import Column, Integer\nfrom sqlalchemy.orm import declarative_base\nBase = declarative_base()\nclass User(Base):\n    __tablename__ = 'users'\n    id = Column(Integer, primary_key=True)",
                "db.py": "from sqlalchemy.ext.asyncio import create_async_engine\nengine = create_async_engine('sqlite+aiosqlite:///test.db')",
            }
        )
        result = validate_database(files)
        assert result.category == "database"
        assert result.checks_run > 0

    def test_authentication_validator(self):
        from validation_engine.validators import validate_authentication

        files = ProjectFiles(
            files={
                "auth.py": "from jose import jwt\nfrom passlib.context import CryptContext\npwd_context = CryptContext(schemes=['bcrypt'])\ntoken = jwt.encode({'sub': 'user'}, 'secret')",
            }
        )
        result = validate_authentication(files)
        assert result.category == "authentication"
        assert result.checks_run > 0

    def test_documentation_validator(self):
        from validation_engine.validators import validate_documentation

        files = ProjectFiles(
            files={
                "README.md": "# Test Project\n\n## Installation\n\n```bash\npip install -r requirements.txt\n```\n\n## Usage\n\nRun the app.",
            }
        )
        result = validate_documentation(files)
        assert result.category == "documentation"
        assert result.checks_run > 0

    def test_docker_validator(self):
        from validation_engine.validators import validate_docker

        files = ProjectFiles(
            files={
                "Dockerfile": "FROM python:3.11-slim\nEXPOSE 8000\nCMD python main.py",
                "docker-compose.yml": "services:\n  web:\n    build: .",
            }
        )
        result = validate_docker(files)
        assert result.category == "docker"
        assert result.checks_run > 0


class TestValidationEngine:
    """Test ValidationEngine orchestration."""

    def test_validate_all_categories(self):
        engine = ValidationEngine()
        files = ProjectFiles(
            files={
                "main.py": "from fastapi import FastAPI\napp = FastAPI()\napp.include_router(router)",
                "requirements.txt": "fastapi\nuvicorn\nsqlalchemy\n",
                "models.py": "from sqlalchemy import Column, Integer\nfrom sqlalchemy.orm import declarative_base\nBase = declarative_base()\nclass User(Base):\n    __tablename__ = 'users'\n    id = Column(Integer, primary_key=True)",
                "db.py": "from sqlalchemy.ext.asyncio import create_async_engine\nengine = create_async_engine('sqlite+aiosqlite:///test.db')",
                "auth.py": "from jose import jwt\nfrom passlib.context import CryptContext",
                "README.md": "# Test\n\n## Installation\n\npip install -r requirements.txt",
                "Dockerfile": "FROM python:3.11\nEXPOSE 8000\nCMD python main.py",
                "docker-compose.yml": "services:\n  web:\n    build: .",
            },
            agent_outputs={
                "project_manager": {},
                "solution_architect": {},
                "database_engineer": {},
                "api_designer": {},
                "backend_developer": {},
                "security_engineer": {},
                "qa_engineer": {},
                "frontend_developer": {},
                "code_reviewer": {},
                "documentation_writer": {},
                "devops_engineer": {},
            },
        )
        report = engine.validate(
            project_files=files,
            project_id=1,
            project_title="Test Project",
        )
        assert report.project_id == 1
        assert report.project_title == "Test Project"
        assert report.overall_status in (ValidationStatus.PASS, ValidationStatus.FAIL)
        assert len(report.categories) == 6
        assert report.production_readiness_score >= 0
        assert report.production_readiness_score <= 100

    def test_validate_single_category(self):
        engine = ValidationEngine()
        files = ProjectFiles(
            files={
                "main.py": "from fastapi import FastAPI\napp = FastAPI()",
            }
        )
        report = engine.validate(
            project_files=files,
            project_id=1,
            project_title="Test",
            categories=["fastapi"],
        )
        assert len(report.categories) == 1
        assert report.categories[0].category == "fastapi"

    def test_validate_from_bundle(self):
        engine = ValidationEngine()
        report = engine.validate_from_bundle(
            project_id=1,
            project_title="Bundle Test",
            generated_files=[
                {"path": "main.py", "content": "from fastapi import FastAPI\napp = FastAPI()"},
                {"path": "requirements.txt", "content": "fastapi\nuvicorn"},
            ],
            agent_outputs={"project_manager": {}},
            categories=["source_code", "fastapi"],
        )
        assert report.project_id == 1
        assert len(report.categories) == 2


class TestValidatorRegistry:
    """Test validator registry."""

    def test_all_validators_registered(self):
        expected = {
            "source_code",
            "fastapi",
            "database",
            "authentication",
            "documentation",
            "docker",
        }
        actual = set(VALIDATOR_REGISTRY.keys())
        assert expected.issubset(actual)

    def test_validators_are_callable(self):
        for name, fn in VALIDATOR_REGISTRY.items():
            assert callable(fn), f"{name} is not callable"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])