"""
Tests for Validation Engine — Phase 4.2
"""
from __future__ import annotations

import pytest

from validation_engine.engine import ValidationEngine
from validation_engine.schemas import (
    ProjectFiles,
    ValidationIssue,
    ValidationSeverity,
    ValidationStatus,
)


class TestValidationEngineSchemas:
    """Test validation schemas."""

    def test_validation_issue(self):
        issue = ValidationIssue(
            category="test",
            severity=ValidationSeverity.ERROR,
            code="TEST_ERROR",
            message="Something went wrong",
            file="main.py",
            line=10,
            recommendation="Fix it",
        )
        assert issue.severity == ValidationSeverity.ERROR
        assert issue.file == "main.py"

    def test_category_result(self):
        from validation_engine.schemas import CategoryResult

        result = CategoryResult(
            category="test",
            status=ValidationStatus.PASS,
            score=100,
            checks_run=5,
            checks_passed=5,
        )
        assert result.error_count == 0
        assert result.warning_count == 0

    def test_category_result_with_errors(self):
        from validation_engine.schemas import CategoryResult

        result = CategoryResult(
            category="test",
            status=ValidationStatus.FAIL,
            score=50,
            checks_run=10,
            checks_passed=5,
            issues=[
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
            ],
        )
        assert result.error_count == 1
        assert result.warning_count == 1

    def test_validation_report_compute(self):
        from validation_engine.schemas import ValidationReport, CategoryResult

        cat1 = CategoryResult(
            category="source_code",
            status=ValidationStatus.PASS,
            score=100,
            checks_run=5,
            checks_passed=5,
        )
        cat2 = CategoryResult(
            category="fastapi",
            status=ValidationStatus.FAIL,
            score=50,
            checks_run=4,
            checks_passed=2,
            issues=[
                ValidationIssue(
                    category="fastapi",
                    severity=ValidationSeverity.ERROR,
                    code="NO_FASTAPI",
                    message="No FastAPI app",
                )
            ],
        )

        report = ValidationReport.compute(1, "Test Project", [cat1, cat2])

        assert report.project_id == 1
        assert report.overall_status == ValidationStatus.FAIL
        assert report.production_readiness_score == 75
        assert report.total_errors == 1
        assert report.total_warnings == 0
        assert "FAIL" in report.summary


class TestProjectFiles:
    """Test ProjectFiles helper methods."""

    def test_get_and_find(self):
        files = ProjectFiles(
            files={
                "main.py": "from fastapi import FastAPI\napp = FastAPI()",
                "models.py": "class User: pass",
                "README.md": "# Project",
            }
        )
        assert files.get("main.py") is not None
        assert files.get("nonexistent.py") is None
        assert "main.py" in files.find("main")
        assert "models.py" in files.find("model")
        assert len(files.find("xyz")) == 0

    def test_content_of(self):
        files = ProjectFiles(files={"test.py": "print('hello')"})
        assert files.content_of("test.py") == "print('hello')"
        assert files.content_of("missing.py") == ""


class TestSourceCodeValidator:
    """Test source code validation."""

    def test_missing_main_py(self):
        files = ProjectFiles(files={"models.py": "class User: pass"})
        from validation_engine.validators import validate_source_code

        result = validate_source_code(files)
        assert result.category == "source_code"
        assert any(i.code == "MISSING_FILE" for i in result.issues)

    def test_missing_requirements(self):
        files = ProjectFiles(files={"main.py": "app = FastAPI()"})
        from validation_engine.validators import validate_source_code

        result = validate_source_code(files)
        assert any(i.code == "MISSING_FILE" and "requirements" in i.message.lower() for i in result.issues)

    def test_hardcoded_secret_detection(self):
        files = ProjectFiles(files={
            "config.py": 'SECRET_KEY = "super-secret-key-123"',
            "main.py": "app = FastAPI()",
        })
        from validation_engine.validators import validate_source_code

        result = validate_source_code(files)
        assert any(i.code == "HARDCODED_SECRET" for i in result.issues)

    def test_syntax_error_detection(self):
        files = ProjectFiles(files={"bad.py": "def foo(\n  pass"})  # Missing closing paren
        from validation_engine.validators import validate_source_code

        result = validate_source_code(files)
        assert any(i.code == "SYNTAX_ERROR" for i in result.issues)

    def test_no_env_file_warning(self):
        files = ProjectFiles(files={"main.py": "app = FastAPI()"})
        from validation_engine.validators import validate_source_code

        result = validate_source_code(files)
        assert any(i.code == "MISSING_ENV" for i in result.issues)


class TestFastAPIValidator:
    """Test FastAPI validation."""

    def test_no_main_py(self):
        files = ProjectFiles(files={"models.py": "class User: pass"})
        from validation_engine.validators import validate_fastapi

        result = validate_fastapi(files)
        assert result.category == "fastapi"
        assert any(i.code == "NO_MAIN" for i in result.issues)

    def test_no_fastapi_instance(self):
        files = ProjectFiles(files={"main.py": "print('hello')"})
        from validation_engine.validators import validate_fastapi

        result = validate_fastapi(files)
        assert any(i.code == "NO_FASTAPI_APP" for i in result.issues)

    def test_no_routers_warning(self):
        files = ProjectFiles(files={"main.py": "from fastapi import FastAPI\napp = FastAPI()"})
        from validation_engine.validators import validate_fastapi

        result = validate_fastapi(files)
        assert any(i.code == "NO_ROUTERS" for i in result.issues)

    def test_no_cors_warning(self):
        files = ProjectFiles(files={"main.py": "from fastapi import FastAPI\napp = FastAPI()\napp.include_router(router)"})
        from validation_engine.validators import validate_fastapi

        result = validate_fastapi(files)
        assert any(i.code == "NO_CORS" for i in result.issues)

    def test_valid_fastapi(self):
        files = ProjectFiles(files={
            "main.py": (
                "from fastapi import FastAPI\n"
                "from fastapi.middleware.cors import CORSMiddleware\n"
                "app = FastAPI()\n"
                "app.add_middleware(CORSMiddleware, allow_origins=['*'])\n"
                "app.include_router(router)\n"
            ),
            "router.py": "from fastapi import APIRouter\nrouter = APIRouter()\n@router.get('/items')\ndef get_items(): pass",
        })
        from validation_engine.validators import validate_fastapi

        result = validate_fastapi(files)
        assert result.status == ValidationStatus.PASS


class TestDatabaseValidator:
    """Test database validation."""

    def test_no_models(self):
        files = ProjectFiles(files={"main.py": "app = FastAPI()"})
        from validation_engine.validators import validate_database

        result = validate_database(files)
        assert any(i.code == "NO_SQLALCHEMY_MODELS" for i in result.issues)

    def test_no_declarative_base_warning(self):
        files = ProjectFiles(files={
            "models.py": "from sqlalchemy import Column, Integer\nclass User: pass",
        })
        from validation_engine.validators import validate_database

        result = validate_database(files)
        assert any(i.code == "NO_DECLARATIVE_BASE" for i in result.issues)

    def test_sync_db_warning(self):
        files = ProjectFiles(files={
            "db.py": "from sqlalchemy import create_engine\nengine = create_engine('sqlite:///test.db')",
            "models.py": "from sqlalchemy.orm import declarative_base\nBase = declarative_base()\nclass User(Base): pass",
        })
        from validation_engine.validators import validate_database

        result = validate_database(files)
        assert any(i.code == "SYNC_DB" for i in result.issues)

    def test_no_migrations_warning(self):
        files = ProjectFiles(files={
            "db.py": "from sqlalchemy.ext.asyncio import create_async_engine\nengine = create_async_engine('sqlite+aiosqlite:///test.db')",
            "models.py": "from sqlalchemy.orm import declarative_base\nBase = declarative_base()\nclass User(Base): pass",
        })
        from validation_engine.validators import validate_database

        result = validate_database(files)
        assert any(i.code == "NO_MIGRATIONS" for i in result.issues)

    def test_no_foreign_keys_info(self):
        files = ProjectFiles(files={
            "models.py": "from sqlalchemy.orm import declarative_base\nBase = declarative_base()\nclass User(Base): pass",
            "db.py": "from sqlalchemy.ext.asyncio import create_async_engine\nengine = create_async_engine('sqlite+aiosqlite:///test.db')",
        })
        from validation_engine.validators import validate_database

        result = validate_database(files)
        assert any(i.code == "NO_FOREIGN_KEYS" for i in result.issues)


class TestAuthValidator:
    """Test authentication validation."""

    def test_no_jwt_error(self):
        files = ProjectFiles(files={"auth.py": "def login(): pass"})
        from validation_engine.validators import validate_authentication

        result = validate_authentication(files)
        assert any(i.code == "NO_JWT" for i in result.issues)

    def test_no_password_hashing_error(self):
        files = ProjectFiles(files={"auth.py": "from jose import jwt"})
        from validation_engine.validators import validate_authentication

        result = validate_authentication(files)
        assert any(i.code == "NO_PASSWORD_HASHING" for i in result.issues)

    def test_no_token_expiry_warning(self):
        files = ProjectFiles(files={"auth.py": "from jose import jwt\nfrom passlib.context import CryptContext"})
        from validation_engine.validators import validate_authentication

        result = validate_authentication(files)
        assert any(i.code == "NO_TOKEN_EXPIRY" for i in result.issues)

    def test_no_ownership_check_warning(self):
        files = ProjectFiles(files={
            "auth.py": "from jose import jwt\nfrom passlib.context import CryptContext\nACCESS_TOKEN_EXPIRE_MINUTES = 30",
            "router.py": "@router.get('/items')\ndef get_items(): pass",
        })
        from validation_engine.validators import validate_authentication

        result = validate_authentication(files)
        assert any(i.code == "NO_OWNERSHIP_CHECK" for i in result.issues)

    def test_no_auth_dependency_warning(self):
        files = ProjectFiles(files={
            "auth.py": "from jose import jwt\nfrom passlib.context import CryptContext\nACCESS_TOKEN_EXPIRE_MINUTES = 30",
            "router.py": "def get_items(): pass",
        })
        from validation_engine.validators import validate_authentication

        result = validate_authentication(files)
        assert any(i.code == "NO_AUTH_DEPENDENCY" for i in result.issues)

    def test_valid_auth(self):
        files = ProjectFiles(files={
            "auth.py": (
                "from jose import jwt\n"
                "from passlib.context import CryptContext\n"
                "ACCESS_TOKEN_EXPIRE_MINUTES = 30\n"
                "pwd_context = CryptContext(schemes=['bcrypt'])\n"
                "def get_current_user(): pass"
            ),
            "router.py": "current_user = Depends(get_current_user)",
        })
        from validation_engine.validators import validate_authentication

        result = validate_authentication(files)
        assert result.status == ValidationStatus.PASS


class TestDocumentationValidator:
    """Test documentation validation."""

    def test_no_readme_error(self):
        files = ProjectFiles(files={"main.py": "app = FastAPI()"})
        from validation_engine.validators import validate_documentation

        result = validate_documentation(files)
        assert any(i.code == "NO_README" for i in result.issues)

    def test_thin_readme_warning(self):
        files = ProjectFiles(files={"README.md": "Short"})
        from validation_engine.validators import validate_documentation

        result = validate_documentation(files)
        assert any(i.code == "THIN_README" for i in result.issues)

    def test_no_install_guide_warning(self):
        files = ProjectFiles(files={"README.md": "# Project\n\nDescription here.\n\n## Features"})
        from validation_engine.validators import validate_documentation

        result = validate_documentation(files)
        assert any(i.code == "NO_INSTALL_GUIDE" for i in result.issues)

    def test_no_api_docs_info(self):
        files = ProjectFiles(files={"README.md": "# Project\n\n## Installation\n`pip install -r requirements.txt`"})
        from validation_engine.validators import validate_documentation

        result = validate_documentation(files)
        assert any(i.code == "NO_API_DOCS" for i in result.issues)

    def test_no_deploy_guide_info(self):
        files = ProjectFiles(files={
            "README.md": "# Project\n\n## Installation\n`pip install -r requirements.txt`\n\n## API\nSee docs"
        })
        from validation_engine.validators import validate_documentation

        result = validate_documentation(files)
        assert any(i.code == "NO_DEPLOY_GUIDE" for i in result.issues)


class TestDockerValidator:
    """Test Docker validation."""

    def test_no_dockerfile_warning(self):
        files = ProjectFiles(files={"main.py": "app = FastAPI()"})
        from validation_engine.validators import validate_docker

        result = validate_docker(files)
        assert any(i.code == "NO_DOCKERFILE" for i in result.issues)

    def test_no_from_error(self):
        files = ProjectFiles(files={"Dockerfile": "CMD python main.py"})
        from validation_engine.validators import validate_docker

        result = validate_docker(files)
        assert any(i.code == "NO_FROM" for i in result.issues)

    def test_no_expose_warning(self):
        files = ProjectFiles(files={"Dockerfile": "FROM python:3.11\nCMD python main.py"})
        from validation_engine.validators import validate_docker

        result = validate_docker(files)
        assert any(i.code == "NO_EXPOSE" for i in result.issues)

    def test_no_compose_warning(self):
        files = ProjectFiles(files={"Dockerfile": "FROM python:3.11\nEXPOSE 8000\nCMD python main.py"})
        from validation_engine.validators import validate_docker

        result = validate_docker(files)
        assert any(i.code == "NO_COMPOSE" for i in result.issues)

    def test_invalid_compose_error(self):
        files = ProjectFiles(files={
            "Dockerfile": "FROM python:3.11\nEXPOSE 8000\nCMD python main.py",
            "docker-compose.yml": "version: '3.8'\n# missing services:",
        })
        from validation_engine.validators import validate_docker

        result = validate_docker(files)
        assert any(i.code == "INVALID_COMPOSE" for i in result.issues)

    def test_no_dockerignore_info(self):
        files = ProjectFiles(files={
            "Dockerfile": "FROM python:3.11\nEXPOSE 8000\nCMD python main.py",
            "docker-compose.yml": "services:\n  web:\n    build: .",
        })
        from validation_engine.validators import validate_docker

        result = validate_docker(files)
        assert any(i.code == "NO_DOCKERIGNORE" for i in result.issues)


class TestValidationEngine:
    """Test the full validation engine."""

    def test_validate_all_categories(self):
        files = ProjectFiles(
            files={
                "main.py": (
                    "from fastapi import FastAPI\n"
                    "from fastapi.middleware.cors import CORSMiddleware\n"
                    "app = FastAPI()\n"
                    "app.add_middleware(CORSMiddleware, allow_origins=['*'])\n"
                    "app.include_router(router)\n"
                ),
                "router.py": "from fastapi import APIRouter\nrouter = APIRouter()\n@router.get('/items')\ndef get_items(): pass",
                "models.py": (
                    "from sqlalchemy.orm import declarative_base\n"
                    "from sqlalchemy import Column, Integer, String, ForeignKey\n"
                    "Base = declarative_base()\n"
                    "class User(Base):\n"
                    "    __tablename__ = 'users'\n"
                    "    id = Column(Integer, primary_key=True)\n"
                    "    name = Column(String)"
                ),
                "db.py": (
                    "from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession\n"
                    "engine = create_async_engine('sqlite+aiosqlite:///test.db')"
                ),
                "auth.py": (
                    "from jose import jwt\n"
                    "from passlib.context import CryptContext\n"
                    "ACCESS_TOKEN_EXPIRE_MINUTES = 30\n"
                    "pwd_context = CryptContext(schemes=['bcrypt'])\n"
                    "def get_current_user(): pass"
                ),
                "requirements.txt": "fastapi\nuvicorn\nsqlalchemy\n",
                "README.md": "# Project\n\n## Installation\n`pip install -r requirements.txt`\n\n## API\nSee docs",
                "Dockerfile": "FROM python:3.11\nEXPOSE 8000\nCMD python main.py",
                "docker-compose.yml": "services:\n  web:\n    build: .",
                ".dockerignore": "*.pyc\n__pycache__",
            }
        )
        engine = ValidationEngine()
        report = engine.validate(files, 1, "Test Project")

        assert report.project_id == 1
        assert report.production_readiness_score > 50
        assert len(report.categories) == 6  # All validators run
        cat_names = {c.category for c in report.categories}
        assert cat_names == {"source_code", "fastapi", "database", "authentication", "documentation", "docker"}

    def test_validate_selected_categories(self):
        files = ProjectFiles(files={"main.py": "app = FastAPI()"})
        engine = ValidationEngine()
        report = engine.validate(files, 1, "Test", categories=["fastapi", "docker"])

        assert len(report.categories) == 2
        cat_names = {c.category for c in report.categories}
        assert cat_names == {"fastapi", "docker"}


class TestValidationFromBundle:
    """Test validate_from_bundle convenience method."""

    def test_validate_from_bundle(self):
        engine = ValidationEngine()
        report = engine.validate_from_bundle(
            project_id=1,
            project_title="Bundle Test",
            generated_files=[
                {"path": "main.py", "content": "from fastapi import FastAPI\napp = FastAPI()"},
                {"path": "requirements.txt", "content": "fastapi\nuvicorn"},
            ],
            agent_outputs={
                "project_manager": {"goals": ["goal1"]},
            },
        )
        assert report.project_id == 1
        assert report.project_title == "Bundle Test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])