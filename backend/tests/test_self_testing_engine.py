"""
Tests for Testing Engine — Phase 4.4
"""
from __future__ import annotations

import pytest

from testing_engine.schemas import (
    TestStatus,
    TestResult,
    TestingReport,
    TestingRequest,
)
from testing_engine.engine import TestingEngine
from testing_engine.tests import TEST_REGISTRY


class TestTestingSchemas:
    """Test testing engine schemas."""

    def test_test_status_enum(self):
        assert TestStatus.PASS == "pass"
        assert TestStatus.FAIL == "fail"
        assert TestStatus.WARN == "warn"
        assert TestStatus.SKIPPED == "skipped"

    def test_test_result(self):
        result = TestResult(
            test_id="T01",
            name="Test Name",
            category="compilation",
            status=TestStatus.PASS,
            message="Success",
            recommendations=["Fix this"],
            duration_ms=100.0,
        )
        assert result.test_id == "T01"
        assert result.status == TestStatus.PASS

    def test_testing_report_compute(self):
        results = [
            TestResult(test_id="T01", name="Test 1", category="cat", status=TestStatus.PASS, message="OK"),
            TestResult(test_id="T02", name="Test 2", category="cat", status=TestStatus.FAIL, message="Fail"),
            TestResult(test_id="T03", name="Test 3", category="cat", status=TestStatus.WARN, message="Warn"),
            TestResult(test_id="T04", name="Test 4", category="cat", status=TestStatus.SKIPPED, message="Skip"),
        ]
        report = TestingReport.compute(1, "Test Project", results)
        assert report.project_id == 1
        assert report.project_title == "Test Project"
        assert report.overall_status == TestStatus.FAIL
        assert report.passed == 1
        assert report.failed == 1
        assert report.warned == 1
        assert report.skipped == 1
        assert report.production_ready is False
        assert report.score == 25  # 1/4 * 100

    def test_testing_request(self):
        req = TestingRequest(project_id=1, test_ids=["T01", "T02"])
        assert req.project_id == 1
        assert req.test_ids == ["T01", "T02"]


class TestTestFunctions:
    """Test individual test functions."""

    def test_requirements(self):
        from testing_engine.tests import test_requirements

        files = {
            "requirements.txt": "fastapi\nuvicorn\nsqlalchemy\npydantic\n",
        }
        result = test_requirements(files)
        assert result.test_id == "T01"
        assert result.status == TestStatus.PASS

    def test_requirements_missing(self):
        from testing_engine.tests import test_requirements

        files = {}
        result = test_requirements(files)
        assert result.test_id == "T01"
        assert result.status == TestStatus.FAIL
        assert "requirements.txt not found" in result.message

    def test_folder_structure(self):
        from testing_engine.tests import test_folder_structure

        files = {
            "main.py": "app = FastAPI()",
            "models/user.py": "class User: pass",
            "api/router.py": "router = APIRouter()",
        }
        result = test_folder_structure(files)
        assert result.test_id == "T02"
        assert result.status == TestStatus.PASS

    def test_compilation(self):
        from testing_engine.tests import test_compilation

        files = {
            "main.py": "print('hello')",
            "models.py": "class User: pass",
        }
        result = test_compilation(files)
        assert result.test_id == "T03"
        assert result.status == TestStatus.PASS

    def test_compilation_syntax_error(self):
        from testing_engine.tests import test_compilation

        files = {
            "main.py": "print('hello'",  # Missing closing paren
        }
        result = test_compilation(files)
        assert result.test_id == "T03"
        assert result.status == TestStatus.FAIL

    def test_fastapi_startup(self):
        from testing_engine.tests import test_fastapi_startup

        files = {
            "main.py": "from fastapi import FastAPI\napp = FastAPI()\napp.include_router(router)\nfrom fastapi.middleware.cors import CORSMiddleware\napp.add_middleware(CORSMiddleware, allow_origins=['*'])",
        }
        result = test_fastapi_startup(files)
        assert result.test_id == "T04"
        assert result.status == TestStatus.PASS

    def test_database_init(self):
        from testing_engine.tests import test_database_init

        files = {
            "db.py": "from sqlalchemy.ext.asyncio import create_async_engine\nfrom sqlalchemy.orm import declarative_base\nengine = create_async_engine('sqlite+aiosqlite:///test.db')\nBase = declarative_base()\nSession = ...",
        }
        result = test_database_init(files)
        assert result.test_id == "T05"
        assert result.status == TestStatus.PASS

    def test_authentication(self):
        from testing_engine.tests import test_authentication

        files = {
            "auth.py": "from jose import jwt\nfrom passlib.context import CryptContext\npwd_context = CryptContext(schemes=['bcrypt'])\nBearer token auth\nOAuth2PasswordBearer\n",
        }
        result = test_authentication(files)
        assert result.test_id == "T06"
        assert result.status == TestStatus.PASS

    def test_crud_apis(self):
        from testing_engine.tests import test_crud_apis

        files = {
            "api/router.py": "@router.get('/')\ndef get_all(): pass\n@router.post('/')\ndef create(): pass\n@router.put('/{id}')\ndef update(id): pass\n@router.delete('/{id}')\ndef delete(id): pass",
        }
        result = test_crud_apis(files)
        assert result.test_id == "T07"
        assert result.status == TestStatus.PASS

    def test_ownership(self):
        from testing_engine.tests import test_ownership

        files = {
            "api/items.py": "if item.owner_id == current_user.id:\n    return item",
        }
        result = test_ownership(files)
        assert result.test_id == "T08"
        assert result.status == TestStatus.PASS

    def test_jwt_validation(self):
        from testing_engine.tests import test_jwt_validation

        files = {
            "auth.py": "from jose import jwt\ntoken = jwt.decode(token_str, 'secret', algorithms=['HS256'])\n# exp is checked automatically",
        }
        result = test_jwt_validation(files)
        assert result.test_id == "T09"
        assert result.status in (TestStatus.PASS, TestStatus.WARN)

    def test_api_endpoints(self):
        from testing_engine.tests import test_api_endpoints

        files = {
            "api/router.py": "@router.get('/items')\ndef get_items(): pass\n@router.get('/items/{id}')\ndef get_item(id): pass",
        }
        result = test_api_endpoints(files)
        assert result.test_id == "T10"
        assert result.status == TestStatus.PASS

    def test_docker_build(self):
        from testing_engine.tests import test_docker_build

        files = {
            "Dockerfile": "FROM python:3.11\nEXPOSE 8000\nCMD python main.py",
            "docker-compose.yml": "services:\n  web:\n    build: .",
        }
        result = test_docker_build(files)
        assert result.test_id == "T11"
        assert result.status == TestStatus.PASS

    def test_readme(self):
        from testing_engine.tests import test_readme

        files = {
            "README.md": """# Test Project

## Installation

pip install -r requirements.txt

## Usage

Run the app.

Quick start guide here.

## Features

- Feature 1
- Feature 2
- Feature 3
- Feature 4
- Feature 5

## API Reference

See API docs.

## License

MIT License.

## Contributing

Pull requests welcome.

## Testing

Run tests with pytest.

## Deployment

Deploy to cloud with Docker.
""",
        }
        result = test_readme(files)
        assert result.test_id == "T12"
        assert result.status == TestStatus.PASS

    def test_readme_missing(self):
        from testing_engine.tests import test_readme

        files = {"main.py": "pass"}
        result = test_readme(files)
        assert result.test_id == "T12"
        assert result.status == TestStatus.FAIL

    def test_generated_files(self):
        from testing_engine.tests import test_generated_files

        files = {
            "main.py": "print('hi')",
            "models.py": "class User: pass",
        }
        result = test_generated_files(files)
        assert result.test_id == "T13"
        assert result.status == TestStatus.PASS

    def test_deployment(self):
        from testing_engine.tests import test_deployment

        files = {
            "Dockerfile": "FROM python:3.11\nCMD python main.py",
            "docker-compose.yml": "services:\n  web:\n    build: .",
        }
        agent_outputs = {
            "devops_engineer": {
                "deployment_guide": "Deploy to cloud",
                "production_env_vars": [{"name": "DB_URL", "description": "Database URL", "is_secret": True}],
                "dockerfile": "FROM python:3.11",
                "docker_compose": "services:\n  web:\n    build: .",
            }
        }
        result = test_deployment(files, agent_outputs=agent_outputs)
        assert result.test_id == "T14"
        assert result.status == TestStatus.PASS

    def test_zip_packaging(self):
        from testing_engine.tests import test_zip_packaging

        files = {
            "main.py": "print('hi')",
            "requirements.txt": "fastapi",
        }
        result = test_zip_packaging(files)
        assert result.test_id == "T15"
        assert result.status == TestStatus.PASS


class TestTestingEngine:
    """Test TestingEngine orchestration."""

    def test_run_all_tests(self):
        engine = TestingEngine()
        files = [
            {"path": "main.py", "content": "from fastapi import FastAPI\napp = FastAPI()"},
            {"path": "requirements.txt", "content": "fastapi\nuvicorn\nsqlalchemy"},
            {"path": "models.py", "content": "class User: pass"},
            {"path": "db.py", "content": "from sqlalchemy.ext.asyncio import create_async_engine"},
            {"path": "auth.py", "content": "from jose import jwt\nfrom passlib.context import CryptContext"},
            {"path": "api/router.py", "content": "@router.get('/')\ndef get(): pass\n@router.post('/')\ndef post(): pass\n@router.put('/{id}')\ndef put(id): pass\n@router.delete('/{id}')\ndef delete(id): pass"},
            {"path": "README.md", "content": "# Test\n\n## Installation\n\npip install -r requirements.txt\n\n## Usage\n\nRun it."},
            {"path": "Dockerfile", "content": "FROM python:3.11\nEXPOSE 8000\nCMD python main.py"},
            {"path": "docker-compose.yml", "content": "services:\n  web:\n    build: ."},
        ]
        agent_outputs = {
            "devops_engineer": {
                "deployment_guide": "Deploy it",
                "production_env_vars": [{"name": "DB_URL", "description": "DB", "is_secret": True}],
                "dockerfile": "FROM python:3.11",
                "docker_compose": "services:\n  web:\n    build: .",
            }
        }
        report = engine.run(
            project_id=1,
            project_title="Test Project",
            generated_files=files,
            agent_outputs=agent_outputs,
        )
        assert report.project_id == 1
        assert report.project_title == "Test Project"
        assert report.overall_status in (TestStatus.PASS, TestStatus.FAIL)
        assert len(report.results) == 15
        assert report.score >= 0
        assert report.score <= 100

    def test_run_specific_tests(self):
        engine = TestingEngine()
        files = [
            {"path": "main.py", "content": "print('hi')"},
        ]
        report = engine.run(
            project_id=1,
            project_title="Test",
            generated_files=files,
            test_ids=["T01", "T03"],
        )
        assert len(report.results) == 2
        assert {r.test_id for r in report.results} == {"T01", "T03"}


class TestRegistry:
    """Test TEST_REGISTRY."""

    def test_all_tests_registered(self):
        expected = {
            "T01", "T02", "T03", "T04", "T05", "T06", "T07",
            "T08", "T09", "T10", "T11", "T12", "T13", "T14", "T15",
        }
        actual = set(TEST_REGISTRY.keys())
        assert expected.issubset(actual)

    def test_tests_are_callable(self):
        for name, fn in TEST_REGISTRY.items():
            assert callable(fn), f"{name} is not callable"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])