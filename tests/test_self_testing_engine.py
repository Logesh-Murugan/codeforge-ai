"""
Tests for Testing Engine — Phase 4.4
"""
from __future__ import annotations

import pytest

from testing_engine.engine import TestingEngine
from testing_engine.schemas import (
    TestResult,
    TestStatus,
    TestingReport,
)
from testing_engine.tests import TEST_REGISTRY


class TestTestingEngineSchemas:
    """Test testing schemas."""

    def test_test_result_pass(self):
        result = TestResult(
            test_id="T01",
            name="Test Name",
            category="test",
            status=TestStatus.PASS,
            message="All good",
        )
        assert result.status == TestStatus.PASS

    def test_test_result_fail(self):
        result = TestResult(
            test_id="T01",
            name="Test Name",
            category="test",
            status=TestStatus.FAIL,
            message="Failed",
            recommendations=["Fix it"],
        )
        assert result.status == TestStatus.FAIL
        assert len(result.recommendations) == 1

    def test_testing_report_compute(self):
        results = [
            TestResult(test_id="T01", name="Test 1", category="cat", status=TestStatus.PASS, message="ok"),
            TestResult(test_id="T02", name="Test 2", category="cat", status=TestStatus.PASS, message="ok"),
            TestResult(test_id="T03", name="Test 3", category="cat", status=TestStatus.FAIL, message="bad"),
        ]
        report = TestingReport.compute(1, "Test Project", results)

        assert report.project_id == 1
        assert report.overall_status == TestStatus.FAIL
        assert report.production_ready is False
        assert report.score == 66  # 2/3 = 66%
        assert report.passed == 2
        assert report.failed == 1
        assert "FAIL" in report.summary

    def test_testing_report_all_pass(self):
        results = [
            TestResult(test_id="T01", name="Test 1", category="cat", status=TestStatus.PASS, message="ok"),
            TestResult(test_id="T02", name="Test 2", category="cat", status=TestStatus.PASS, message="ok"),
        ]
        report = TestingReport.compute(1, "Test Project", results)

        assert report.overall_status == TestStatus.PASS
        assert report.production_ready is True
        assert report.score == 100


class TestIndividualTests:
    """Test individual test functions."""

    def test_T01_requirements_pass(self):
        files = {"requirements.txt": "fastapi\nuvicorn\nsqlalchemy\npydantic\n"}
        from testing_engine.tests import test_requirements

        result = test_requirements(files)
        assert result.test_id == "T01"
        assert result.status == TestStatus.PASS

    def test_T01_requirements_missing(self):
        files = {}
        from testing_engine.tests import test_requirements

        result = test_requirements(files)
        assert result.status == TestStatus.FAIL
        assert "requirements.txt not found" in result.message

    def test_T01_requirements_warn(self):
        files = {"requirements.txt": "fastapi\n"}
        from testing_engine.tests import test_requirements

        result = test_requirements(files)
        assert result.status == TestStatus.WARN
        assert "missing" in result.message.lower()

    def test_T02_folder_structure_pass(self):
        files = {
            "main.py": "app = FastAPI()",
            "models/user.py": "class User: pass",
            "api/routes.py": "router = APIRouter()",
        }
        from testing_engine.tests import test_folder_structure

        result = test_folder_structure(files)
        assert result.status == TestStatus.PASS

    def test_T02_folder_structure_warn(self):
        files = {"main.py": "app = FastAPI()"}
        from testing_engine.tests import test_folder_structure

        result = test_folder_structure(files)
        assert result.status == TestStatus.WARN

    def test_T03_compilation_pass(self):
        files = {"main.py": "print('hello')\n", "models.py": "class User: pass\n"}
        from testing_engine.tests import test_compilation

        result = test_compilation(files)
        assert result.status == TestStatus.PASS

    def test_T03_compilation_fail(self):
        files = {"bad.py": "def foo(\n  pass"}  # Syntax error
        from testing_engine.tests import test_compilation

        result = test_compilation(files)
        assert result.status == TestStatus.FAIL
        assert "syntax error" in result.message.lower()

    def test_T04_fastapi_startup_pass(self):
        files = {
            "main.py": (
                "from fastapi import FastAPI\n"
                "from fastapi.middleware.cors import CORSMiddleware\n"
                "app = FastAPI()\n"
                "app.add_middleware(CORSMiddleware, allow_origins=['*'])\n"
                "app.include_router(router)\n"
            )
        }
        from testing_engine.tests import test_fastapi_startup

        result = test_fastapi_startup(files)
        assert result.status == TestStatus.PASS

    def test_T04_fastapi_startup_fail(self):
        files = {"main.py": "print('no fastapi here')"}
        from testing_engine.tests import test_fastapi_startup

        result = test_fastapi_startup(files)
        assert result.status == TestStatus.FAIL

    def test_T05_database_init_pass(self):
        files = {
            "db.py": (
                "from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession\n"
                "engine = create_async_engine('sqlite+aiosqlite:///test.db')\n"
                "Base = declarative_base()\n"
            )
        }
        from testing_engine.tests import test_database_init

        result = test_database_init(files)
        assert result.status in (TestStatus.PASS, TestStatus.WARN)

    def test_T05_database_init_warn(self):
        files = {"main.py": "app = FastAPI()"}
        from testing_engine.tests import test_database_init

        result = test_database_init(files)
        assert result.status == TestStatus.WARN

    def test_T06_authentication_pass(self):
        files = {
            "auth.py": (
                "from jose import jwt\n"
                "from passlib.context import CryptContext\n"
                "pwd_context = CryptContext(schemes=['bcrypt'])\n"
                "def create_token(): return jwt.encode({}, 'secret')\n"
                "def verify_token(): return jwt.decode('token', 'secret')\n"
                "AUTH_SCHEME = 'Bearer'\n"
            )
        }
        from testing_engine.tests import test_authentication

        result = test_authentication(files)
        assert result.status == TestStatus.PASS

    def test_T06_authentication_fail(self):
        files = {"auth.py": "def login(): pass"}
        from testing_engine.tests import test_authentication

        result = test_authentication(files)
        assert result.status == TestStatus.FAIL

    def test_T07_crud_apis_pass(self):
        files = {
            "router.py": (
                "@router.get('/items')\ndef get_items(): pass\n"
                "@router.post('/items')\ndef create_item(): pass\n"
                "@router.put('/items/{id}')\ndef update_item(): pass\n"
                "@router.delete('/items/{id}')\ndef delete_item(): pass\n"
            )
        }
        from testing_engine.tests import test_crud_apis

        result = test_crud_apis(files)
        assert result.status == TestStatus.PASS

    def test_T07_crud_apis_warn(self):
        files = {"router.py": "@router.get('/items')\ndef get_items(): pass"}
        from testing_engine.tests import test_crud_apis

        result = test_crud_apis(files)
        assert result.status == TestStatus.WARN
        assert "Missing CRUD methods" in result.message

    def test_T08_ownership_pass(self):
        files = {"router.py": "if item.owner_id == current_user.id:\n    return item"}
        from testing_engine.tests import test_ownership

        result = test_ownership(files)
        assert result.status == TestStatus.PASS

    def test_T08_ownership_warn(self):
        files = {"router.py": "owner_id = 123"}
        from testing_engine.tests import test_ownership

        result = test_ownership(files)
        assert result.status == TestStatus.WARN

    def test_T09_jwt_validation_pass(self):
        files = {
            "auth.py": (
                "from jose import jwt\n"
                "def decode_token():\n"
                "    return jwt.decode('token', 'secret', algorithms=['HS256'])\n"
                "def create_token():\n"
                "    return jwt.encode({'exp': 1234567890}, 'secret')\n"
            )
        }
        from testing_engine.tests import test_jwt_validation

        result = test_jwt_validation(files)
        assert result.status == TestStatus.PASS

    def test_T09_jwt_validation_warn(self):
        files = {"auth.py": "from jose import jwt\ndef decode_token(): return jwt.decode('token', 'secret')"}
        from testing_engine.tests import test_jwt_validation

        result = test_jwt_validation(files)
        assert result.status == TestStatus.WARN

    def test_T10_api_endpoints_pass(self):
        files = {
            "router.py": "@router.get('/items')\ndef get_items(): pass\n@router.post('/items')\ndef create(): pass",
        }
        from testing_engine.tests import test_api_endpoints

        result = test_api_endpoints(files)
        assert result.status == TestStatus.PASS

    def test_T10_api_endpoints_duplicate_warn(self):
        files = {
            "router.py": (
                "@router.get('/items')\ndef get_items(): pass\n"
                "@router.get('/items')\ndef get_items2(): pass\n"
            )
        }
        from testing_engine.tests import test_api_endpoints

        result = test_api_endpoints(files)
        assert result.status == TestStatus.WARN
        assert "duplicate" in result.message.lower()

    def test_T11_docker_build_pass(self):
        files = {
            "Dockerfile": "FROM python:3.11\nEXPOSE 8000\nCMD python main.py",
            "docker-compose.yml": "services:\n  web:\n    build: .",
        }
        from testing_engine.tests import test_docker_build

        result = test_docker_build(files)
        assert result.status == TestStatus.PASS

    def test_T11_docker_build_warn(self):
        files = {"Dockerfile": "CMD python main.py"}
        from testing_engine.tests import test_docker_build

        result = test_docker_build(files)
        assert result.status == TestStatus.WARN

    def test_T12_readme_pass(self):
        files = {"README.md": "# Project\n\n## Installation\n`pip install -r requirements.txt`\n\n## Usage\nRun the app"}
        from testing_engine.tests import test_readme

        result = test_readme(files)
        assert result.status == TestStatus.PASS

    def test_T12_readme_fail(self):
        files = {}
        from testing_engine.tests import test_readme

        result = test_readme(files)
        assert result.status == TestStatus.FAIL

    def test_T12_readme_warn(self):
        files = {"README.md": "# Short"}
        from testing_engine.tests import test_readme

        result = test_readme(files)
        assert result.status == TestStatus.WARN

    def test_T13_generated_files_pass(self):
        files = {"main.py": "print('hi')", "models.py": "class User: pass"}
        from testing_engine.tests import test_generated_files

        result = test_generated_files(files)
        assert result.status == TestStatus.PASS

    def test_T13_generated_files_fail(self):
        files = {}
        from testing_engine.tests import test_generated_files

        result = test_generated_files(files)
        assert result.status == TestStatus.FAIL

    def test_T13_generated_files_warn(self):
        files = {"main.py": "", "models.py": "class User: pass"}
        from testing_engine.tests import test_generated_files

        result = test_generated_files(files)
        assert result.status == TestStatus.WARN

    def test_T14_deployment_pass(self):
        files = {
            "Dockerfile": "FROM python:3.11\nEXPOSE 8000\nCMD python main.py",
            "docker-compose.yml": "services:\n  web:\n    build: .",
        }
        agent_outputs = {
            "devops_engineer": {
                "deployment_guide": "Deploy to cloud",
                "production_env_vars": [{"name": "SECRET", "description": "Secret"}],
                "dockerfile": "FROM python...",
                "docker_compose": "services: ...",
            }
        }
        from testing_engine.tests import test_deployment

        result = test_deployment(files, agent_outputs)
        assert result.status == TestStatus.PASS

    def test_T14_deployment_fail(self):
        files = {}
        agent_outputs = {}
        from testing_engine.tests import test_deployment

        result = test_deployment(files, agent_outputs)
        assert result.status == TestStatus.FAIL

    def test_T15_zip_packaging_pass(self):
        files = {"main.py": "print('hi')", "README.md": "# Project"}
        from testing_engine.tests import test_zip_packaging

        result = test_zip_packaging(files)
        assert result.status == TestStatus.PASS
        assert "ZIP packaging successful" in result.message


class TestTestingEngine:
    """Test the TestingEngine orchestration."""

    def test_run_all_tests(self):
        files = [
            {"path": "requirements.txt", "content": "fastapi\nuvicorn\nsqlalchemy\n"},
            {"path": "main.py", "content": "from fastapi import FastAPI\napp = FastAPI()"},
            {"path": "router.py", "content": "@router.get('/items')\ndef get(): pass"},
            {"path": "auth.py", "content": "from jose import jwt\nfrom passlib.context import CryptContext\nACCESS_TOKEN_EXPIRE_MINUTES = 30"},
            {"path": "README.md", "content": "# Project\n\n## Installation\n`pip install`\n\n## Usage\nRun it"},
            {"path": "Dockerfile", "content": "FROM python:3.11\nEXPOSE 8000\nCMD python main.py"},
            {"path": "docker-compose.yml", "content": "services:\n  web:\n    build: ."},
        ]
        agent_outputs = {
            "devops_engineer": {
                "deployment_guide": "Deploy it",
                "production_env_vars": [],
                "dockerfile": "",
                "docker_compose": "",
            }
        }

        engine = TestingEngine()
        report = engine.run(1, "Test Project", files, agent_outputs)

        assert report.project_id == 1
        assert report.project_title == "Test Project"
        assert len(report.results) == 15
        assert report.passed + report.failed + report.warned + report.skipped == 15

    def test_run_selected_tests(self):
        files = [{"path": "requirements.txt", "content": "fastapi\nuvicorn\n"}]
        engine = TestingEngine()
        report = engine.run(1, "Test", files, test_ids=["T01", "T02"])

        assert len(report.results) == 2
        assert all(r.test_id in ["T01", "T02"] for r in report.results)

    def test_run_invalid_test_id(self):
        files = [{"path": "requirements.txt", "content": "fastapi"}]
        engine = TestingEngine()
        report = engine.run(1, "Test", files, test_ids=["T99"])

        # Invalid test ID should be skipped/ignored
        assert len(report.results) == 0


class TestTestRegistry:
    """Test that all expected tests are registered."""

    def test_all_test_ids_present(self):
        expected = {"T01", "T02", "T03", "T04", "T05", "T06", "T07", "T08", "T09", "T10", "T11", "T12", "T13", "T14", "T15"}
        actual = set(TEST_REGISTRY.keys())
        assert actual == expected

    def test_all_tests_callable(self):
        for tid, fn in TEST_REGISTRY.items():
            assert callable(fn), f"Test {tid} is not callable"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])