"""
Tests for Phase 5.1 — Memory Engine Integration Tests

SQLite-backed integration tests that exercise the full CRUD lifecycle
through all 12 domain memory engines with a real database.
Requires ``aiosqlite``.
"""
from __future__ import annotations

import pytest
import pytest_asyncio
from datetime import datetime, timezone
from typing import List

from memory.persistent_schemas import MemoryCategory
from memory.persistent_service import PersistentMemoryService
from memory.services import (
    ProjectMemoryEngine,
    AgentMemoryEngine,
    RequirementMemoryEngine,
    ArchitectureMemoryEngine,
    DatabaseMemoryEngine,
    APIMemoryEngine,
    BackendMemoryEngine,
    FrontendMemoryEngine,
    SecurityMemoryEngine,
    TestingMemoryEngine,
    DeploymentMemoryEngine,
    DocumentationMemoryEngine,
    get_engine,
)


# ── Shared fixture ──────────────────────────────────────────────────────────


class IntegrationBase:
    """
    Base class for integration tests.  Creates an in-memory SQLite DB
    with all tables before each test method.
    """

    @pytest_asyncio.fixture(autouse=True)
    async def setup_db(self):
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from app.db import Base
        # Import target tables to satisfy ForeignKey constraints
        from app.models.user import User
        from app.models.project import Project
        # Ensure models are imported so metadata is populated
        from memory.persistent_models import PersistentProjectMemory, PersistentMemoryVersion
        from memory.models.agent_memory import AgentMemoryEntry
        from memory.models.memory_embedding import MemoryEmbeddingRecord

        self.engine_db = create_async_engine("sqlite+aiosqlite://", echo=False)
        self.TestSessionLocal = async_sessionmaker(
            self.engine_db, expire_on_commit=False,
        )
        async with self.engine_db.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield
        async with self.engine_db.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await self.engine_db.dispose()


# ── Full CRUD Lifecycle per Engine ──────────────────────────────────────────


class TestProjectEngineIntegration(IntegrationBase):

    @pytest.mark.asyncio
    async def test_project_full_lifecycle(self):
        psvc = PersistentMemoryService()
        engine = ProjectMemoryEngine(persistent_service=psvc)

        async with self.TestSessionLocal() as session:
            # Create
            entry = await engine.create(
                project_id=100,
                content="Project kickoff",
                agent_name="project_manager",
                domain_fields={"milestone": "MVP", "project_phase": "init"},
                session=session,
            )
            assert entry.id > 0
            assert entry.category == "project"

            # Read
            fetched = await engine.get(
                project_id=100, entry_id=entry.id, session=session,
            )
            assert fetched is not None
            assert fetched.content == "Project kickoff"

            # Update
            updated = await engine.update(
                project_id=100, entry_id=entry.id,
                content="Updated kickoff",
                change_reason="Sprint review",
                changed_by="product_owner",
                session=session,
            )
            assert updated is not None
            assert updated.version == 2

            # Version history
            versions = await engine.get_versions(
                project_id=100, entry_id=entry.id, session=session,
            )
            assert len(versions) == 2

            # Search
            results = await engine.search(
                project_id=100, query="kickoff", session=session,
            )
            assert len(results) >= 1

            # Count
            count = await engine.count(project_id=100, session=session)
            assert count >= 1

            # Delete
            deleted = await engine.delete(
                project_id=100, entry_id=entry.id, session=session,
            )
            assert deleted is True

            # Verify deleted
            after = await engine.get(
                project_id=100, entry_id=entry.id, session=session,
            )
            assert after is None


class TestAgentEngineIntegration(IntegrationBase):

    @pytest.mark.asyncio
    async def test_agent_full_lifecycle(self):
        psvc = PersistentMemoryService()
        engine = AgentMemoryEngine(persistent_service=psvc)

        async with self.TestSessionLocal() as session:
            entry = await engine.create(
                project_id=200,
                content="Backend code generated",
                agent_name="backend_developer",
                domain_fields={
                    "agent_type": "developer",
                    "model_used": "llama-3.1-70b",
                    "token_count": 1500,
                    "execution_duration_ms": 2500.0,
                },
                session=session,
            )
            assert entry.id > 0

            stats = await engine.get_execution_stats(
                project_id=200, session=session,
            )
            assert stats["total_entries"] == 1
            assert stats["total_tokens"] == 1500


class TestRequirementEngineIntegration(IntegrationBase):

    @pytest.mark.asyncio
    async def test_requirement_with_defaults(self):
        psvc = PersistentMemoryService()
        engine = RequirementMemoryEngine(persistent_service=psvc)

        async with self.TestSessionLocal() as session:
            entry = await engine.create(
                project_id=300,
                content="User authentication via JWT",
                agent_name="business_analyst",
                session=session,
            )
            assert entry.metadata_json.get("priority") == "medium"
            assert entry.metadata_json.get("status") == "draft"

            summary = await engine.get_requirements_summary(
                project_id=300, session=session,
            )
            assert summary["total"] == 1


class TestArchitectureEngineIntegration(IntegrationBase):

    @pytest.mark.asyncio
    async def test_architecture_summary(self):
        psvc = PersistentMemoryService()
        engine = ArchitectureMemoryEngine(persistent_service=psvc)

        async with self.TestSessionLocal() as session:
            await engine.create(
                project_id=400,
                content="Microservice auth component",
                domain_fields={
                    "component_name": "auth-service",
                    "layer": "business",
                    "pattern": "repository",
                    "tech_stack": ["python", "fastapi"],
                },
                session=session,
            )
            summary = await engine.get_architecture_summary(
                project_id=400, session=session,
            )
            assert summary["total"] == 1
            assert "auth-service" in summary["components"]


class TestDatabaseEngineIntegration(IntegrationBase):

    @pytest.mark.asyncio
    async def test_database_defaults_and_schema_map(self):
        psvc = PersistentMemoryService()
        engine = DatabaseMemoryEngine(persistent_service=psvc)

        async with self.TestSessionLocal() as session:
            entry = await engine.create(
                project_id=500,
                content="Users table definition",
                domain_fields={
                    "table_name": "users",
                    "relationships": ["projects"],
                    "indexes": ["idx_users_email"],
                },
                session=session,
            )
            assert entry.metadata_json.get("migration_status") == "pending"
            assert entry.metadata_json.get("db_engine") == "postgresql"

            schema_map = await engine.get_schema_map(
                project_id=500, session=session,
            )
            assert "users" in schema_map["tables"]


class TestAPIEngineIntegration(IntegrationBase):

    @pytest.mark.asyncio
    async def test_api_catalog(self):
        psvc = PersistentMemoryService()
        engine = APIMemoryEngine(persistent_service=psvc)

        async with self.TestSessionLocal() as session:
            await engine.create(
                project_id=600,
                content="GET /api/users",
                domain_fields={
                    "endpoint": "/api/users",
                    "method": "GET",
                    "auth_required": True,
                    "api_version": "v1",
                },
                session=session,
            )
            catalog = await engine.get_api_catalog(
                project_id=600, session=session,
            )
            assert catalog["total"] == 1
            assert "/api/users" in catalog["authenticated_endpoints"]


class TestBackendEngineIntegration(IntegrationBase):

    @pytest.mark.asyncio
    async def test_backend_dependency_map(self):
        psvc = PersistentMemoryService()
        engine = BackendMemoryEngine(persistent_service=psvc)

        async with self.TestSessionLocal() as session:
            entry = await engine.create(
                project_id=700,
                content="def create_user(): ...",
                agent_name="backend_developer",
                domain_fields={
                    "module_name": "auth",
                    "code_type": "service",
                    "framework": "fastapi",
                    "dependencies": ["sqlalchemy", "passlib"],
                },
                session=session,
            )
            assert entry.metadata_json.get("language") == "python"

            dep_map = await engine.get_dependency_map(
                project_id=700, session=session,
            )
            assert "sqlalchemy" in dep_map["dependencies"]


class TestFrontendEngineIntegration(IntegrationBase):

    @pytest.mark.asyncio
    async def test_frontend_component_tree(self):
        psvc = PersistentMemoryService()
        engine = FrontendMemoryEngine(persistent_service=psvc)

        async with self.TestSessionLocal() as session:
            await engine.create(
                project_id=800,
                content="<LoginForm />",
                domain_fields={
                    "component_name": "LoginForm",
                    "component_type": "page",
                    "route_path": "/login",
                    "framework": "react",
                },
                session=session,
            )
            tree = await engine.get_component_tree(
                project_id=800, session=session,
            )
            assert tree["total"] == 1
            assert "/login" in tree["routes"]


class TestSecurityEngineIntegration(IntegrationBase):

    @pytest.mark.asyncio
    async def test_security_dashboard(self):
        psvc = PersistentMemoryService()
        engine = SecurityMemoryEngine(persistent_service=psvc)

        async with self.TestSessionLocal() as session:
            await engine.create(
                project_id=900,
                content="XSS vulnerability in login form",
                agent_name="security_engineer",
                domain_fields={
                    "severity": "high",
                    "vulnerability_type": "XSS",
                    "scan_type": "sast",
                    "affected_component": "frontend/login",
                    "compliance": ["owasp"],
                },
                session=session,
            )
            dashboard = await engine.get_security_dashboard(
                project_id=900, session=session,
            )
            assert dashboard["total"] == 1
            assert dashboard["by_severity"]["high"] == 1


class TestTestingEngineIntegration(IntegrationBase):

    @pytest.mark.asyncio
    async def test_quality_report(self):
        psvc = PersistentMemoryService()
        engine = TestingMemoryEngine(persistent_service=psvc)

        async with self.TestSessionLocal() as session:
            await engine.create(
                project_id=1000,
                content="Unit test results",
                domain_fields={
                    "test_type": "unit",
                    "coverage_percent": 92.5,
                    "pass_rate": 99.0,
                    "total_tests": 150,
                    "failed_tests": 1,
                    "skipped_tests": 3,
                },
                session=session,
            )
            report = await engine.get_quality_report(
                project_id=1000, session=session,
            )
            assert report["total_entries"] == 1
            assert report["avg_coverage_percent"] == 92.5


class TestDeploymentEngineIntegration(IntegrationBase):

    @pytest.mark.asyncio
    async def test_deployment_overview(self):
        psvc = PersistentMemoryService()
        engine = DeploymentMemoryEngine(persistent_service=psvc)

        async with self.TestSessionLocal() as session:
            await engine.create(
                project_id=1100,
                content="Render deployment config",
                agent_name="devops_engineer",
                domain_fields={
                    "environment": "production",
                    "provider": "render",
                    "status": "deployed",
                    "deploy_url": "https://app.render.com",
                    "env_variables": ["DATABASE_URL", "JWT_SECRET"],
                },
                session=session,
            )
            overview = await engine.get_deployment_overview(
                project_id=1100, session=session,
            )
            assert overview["total"] == 1
            assert "DATABASE_URL" in overview["required_env_variables"]


class TestDocumentationEngineIntegration(IntegrationBase):

    @pytest.mark.asyncio
    async def test_documentation_index(self):
        psvc = PersistentMemoryService()
        engine = DocumentationMemoryEngine(persistent_service=psvc)

        async with self.TestSessionLocal() as session:
            await engine.create(
                project_id=1200,
                content="# CodeForge AI\n\nAutonomous engineering platform.",
                agent_name="doc_writer",
                domain_fields={
                    "doc_type": "readme",
                    "audience": "developer",
                    "doc_format": "markdown",
                    "auto_generated": True,
                    "related_files": ["README.md"],
                },
                session=session,
            )
            index = await engine.get_documentation_index(
                project_id=1200, session=session,
            )
            assert index["total"] == 1
            assert index["auto_generated_count"] == 1


# ── Cross-Engine Regression Tests ──────────────────────────────────────────


class TestCrossEngineRegression(IntegrationBase):
    """Verify that entries from different engines are isolated by category."""

    @pytest.mark.asyncio
    async def test_category_isolation(self):
        psvc = PersistentMemoryService()
        project_engine = ProjectMemoryEngine(persistent_service=psvc)
        security_engine = SecurityMemoryEngine(persistent_service=psvc)

        async with self.TestSessionLocal() as session:
            proj_entry = await project_engine.create(
                project_id=5000, content="Project data",
                session=session,
            )
            sec_entry = await security_engine.create(
                project_id=5000, content="Security data",
                session=session,
            )

            # Project engine should not see security entries
            proj_list = await project_engine.list_entries(
                project_id=5000, session=session,
            )
            sec_list = await security_engine.list_entries(
                project_id=5000, session=session,
            )
            assert len(proj_list) == 1
            assert len(sec_list) == 1
            assert proj_list[0].category == "project"
            assert sec_list[0].category == "security"

            # Cross-category get should return None
            cross = await project_engine.get(
                project_id=5000, entry_id=sec_entry.id, session=session,
            )
            assert cross is None

    @pytest.mark.asyncio
    async def test_multi_engine_counts(self):
        psvc = PersistentMemoryService()

        async with self.TestSessionLocal() as session:
            for domain_name in ["project", "agent", "requirement"]:
                engine = get_engine(domain_name)
                engine._psvc = psvc
                await engine.create(
                    project_id=6000,
                    content=f"Entry for {domain_name}",
                    session=session,
                )

            project_count = await ProjectMemoryEngine(
                persistent_service=psvc,
            ).count(project_id=6000, session=session)
            agent_count = await AgentMemoryEngine(
                persistent_service=psvc,
            ).count(project_id=6000, session=session)
            req_count = await RequirementMemoryEngine(
                persistent_service=psvc,
            ).count(project_id=6000, session=session)

            assert project_count == 1
            assert agent_count == 1
            assert req_count == 1
