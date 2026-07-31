"""
Tests for Phase 5.1 — Domain Memory Engines (Unit Tests)

Tests all 12 domain-specific memory engines using mocked
PersistentMemoryService.  No database or network required.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

from memory.persistent_schemas import (
    MemoryCategory,
    PersistentMemoryResponse,
    PersistentMemoryVersionResponse,
)
from memory.services import (
    BaseMemoryEngine,
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
    ENGINE_REGISTRY,
    get_engine,
)


# ── Fixtures ────────────────────────────────────────────────────────────────

def _make_response(
    entry_id: int = 1,
    project_id: int = 42,
    category: str = "project",
    agent_name: str = "system",
    content: str = "Test content",
    metadata_json: Optional[Dict[str, Any]] = None,
    version: int = 1,
) -> PersistentMemoryResponse:
    """Build a PersistentMemoryResponse for testing."""
    now = datetime.now(timezone.utc)
    return PersistentMemoryResponse(
        id=entry_id,
        project_id=project_id,
        category=category,
        agent_name=agent_name,
        content=content,
        metadata_json=metadata_json or {},
        version=version,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def _make_version_response(
    ver_id: int = 1,
    entry_id: int = 1,
    project_id: int = 42,
    category: str = "project",
    content: str = "Version content",
    version: int = 1,
) -> PersistentMemoryVersionResponse:
    """Build a PersistentMemoryVersionResponse for testing."""
    now = datetime.now(timezone.utc)
    return PersistentMemoryVersionResponse(
        id=ver_id,
        entry_id=entry_id,
        project_id=project_id,
        category=category,
        content=content,
        metadata_json={},
        version=version,
        change_reason="test",
        changed_by="tester",
        created_at=now,
    )


def _mock_psvc(**overrides):
    """Create a mocked PersistentMemoryService."""
    psvc = MagicMock()
    psvc.create_entry = AsyncMock(
        return_value=overrides.get("create", _make_response())
    )
    psvc.get_entry = AsyncMock(
        return_value=overrides.get("get", _make_response())
    )
    psvc.list_entries = AsyncMock(
        return_value=overrides.get("list", [_make_response()])
    )
    psvc.update_entry = AsyncMock(
        return_value=overrides.get("update", _make_response(version=2))
    )
    psvc.delete_entry = AsyncMock(
        return_value=overrides.get("delete", True)
    )
    psvc.search_entries = AsyncMock(
        return_value=overrides.get("search", [_make_response()])
    )
    psvc.get_version_history = AsyncMock(
        return_value=overrides.get("versions", [_make_version_response()])
    )
    psvc.count_entries = AsyncMock(
        return_value=overrides.get("count", 1)
    )
    return psvc


# ── Engine Registry Tests ───────────────────────────────────────────────────


class TestEngineRegistry:
    """Test ENGINE_REGISTRY and get_engine factory."""

    def test_all_12_engines_registered(self):
        expected_domains = {
            "project", "agent", "requirement", "architecture",
            "database", "api", "backend", "frontend",
            "security", "testing", "deployment", "documentation",
        }
        assert set(ENGINE_REGISTRY.keys()) == expected_domains

    def test_get_engine_valid_domain(self):
        for domain in ENGINE_REGISTRY:
            engine = get_engine(domain)
            assert isinstance(engine, BaseMemoryEngine)

    def test_get_engine_case_insensitive(self):
        engine = get_engine("PROJECT")
        assert isinstance(engine, ProjectMemoryEngine)

    def test_get_engine_invalid_domain(self):
        with pytest.raises(ValueError, match="Unknown memory domain"):
            get_engine("nonexistent")

    def test_each_engine_has_unique_category(self):
        categories = set()
        for cls in ENGINE_REGISTRY.values():
            inst = cls()
            categories.add(inst.CATEGORY)
        assert len(categories) == 12


# ── Base Engine Tests ───────────────────────────────────────────────────────


class TestBaseEngineCreate:
    """Test BaseMemoryEngine.create through a concrete subclass."""

    @pytest.mark.asyncio
    async def test_create_entry(self):
        psvc = _mock_psvc(
            create=_make_response(category="project", content="Phase 1 kickoff")
        )
        engine = ProjectMemoryEngine(persistent_service=psvc)
        result = await engine.create(
            project_id=42,
            content="Phase 1 kickoff",
            agent_name="project_manager",
        )
        assert result.content == "Phase 1 kickoff"
        assert result.category == "project"
        psvc.create_entry.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_with_domain_fields(self):
        psvc = _mock_psvc(
            create=_make_response(
                category="project",
                metadata_json={"milestone": "MVP", "status": "active"},
            )
        )
        engine = ProjectMemoryEngine(persistent_service=psvc)
        result = await engine.create(
            project_id=42,
            content="Project milestone",
            domain_fields={"milestone": "MVP", "status": "active"},
        )
        assert result.metadata_json.get("milestone") == "MVP"


class TestBaseEngineGet:
    """Test BaseMemoryEngine.get category scoping."""

    @pytest.mark.asyncio
    async def test_get_entry_correct_category(self):
        psvc = _mock_psvc(get=_make_response(category="project"))
        engine = ProjectMemoryEngine(persistent_service=psvc)
        result = await engine.get(project_id=42, entry_id=1)
        assert result is not None
        assert result.category == "project"

    @pytest.mark.asyncio
    async def test_get_entry_wrong_category_returns_none(self):
        psvc = _mock_psvc(get=_make_response(category="security"))
        engine = ProjectMemoryEngine(persistent_service=psvc)
        result = await engine.get(project_id=42, entry_id=1)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_entry_not_found(self):
        psvc = _mock_psvc(get=None)
        engine = ProjectMemoryEngine(persistent_service=psvc)
        result = await engine.get(project_id=42, entry_id=999)
        assert result is None


class TestBaseEngineUpdate:
    """Test BaseMemoryEngine.update with version bumps."""

    @pytest.mark.asyncio
    async def test_update_entry(self):
        psvc = _mock_psvc(
            get=_make_response(category="project"),
            update=_make_response(category="project", version=2, content="Updated"),
        )
        engine = ProjectMemoryEngine(persistent_service=psvc)
        result = await engine.update(
            project_id=42, entry_id=1, content="Updated",
        )
        assert result is not None
        assert result.version == 2

    @pytest.mark.asyncio
    async def test_update_nonexistent_returns_none(self):
        psvc = _mock_psvc(get=None)
        engine = ProjectMemoryEngine(persistent_service=psvc)
        result = await engine.update(
            project_id=42, entry_id=999, content="Updated",
        )
        assert result is None


class TestBaseEngineDelete:
    """Test BaseMemoryEngine.delete with category scoping."""

    @pytest.mark.asyncio
    async def test_delete_entry(self):
        psvc = _mock_psvc(
            get=_make_response(category="project"),
            delete=True,
        )
        engine = ProjectMemoryEngine(persistent_service=psvc)
        result = await engine.delete(project_id=42, entry_id=1)
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_wrong_category(self):
        psvc = _mock_psvc(get=_make_response(category="security"))
        engine = ProjectMemoryEngine(persistent_service=psvc)
        result = await engine.delete(project_id=42, entry_id=1)
        assert result is False


class TestBaseEngineSearch:
    """Test BaseMemoryEngine.search."""

    @pytest.mark.asyncio
    async def test_search_entries(self):
        psvc = _mock_psvc(
            search=[
                _make_response(content="JWT auth"),
                _make_response(content="OAuth2 setup"),
            ]
        )
        engine = SecurityMemoryEngine(persistent_service=psvc)
        results = await engine.search(project_id=42, query="auth")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_empty_results(self):
        psvc = _mock_psvc(search=[])
        engine = SecurityMemoryEngine(persistent_service=psvc)
        results = await engine.search(project_id=42, query="nonexistent")
        assert results == []


class TestBaseEngineVersions:
    """Test BaseMemoryEngine.get_versions."""

    @pytest.mark.asyncio
    async def test_get_versions(self):
        psvc = _mock_psvc(
            get=_make_response(category="project"),
            versions=[
                _make_version_response(version=2),
                _make_version_response(version=1),
            ],
        )
        engine = ProjectMemoryEngine(persistent_service=psvc)
        versions = await engine.get_versions(project_id=42, entry_id=1)
        assert len(versions) == 2
        assert versions[0].version == 2

    @pytest.mark.asyncio
    async def test_get_versions_wrong_category_empty(self):
        psvc = _mock_psvc(get=_make_response(category="security"))
        engine = ProjectMemoryEngine(persistent_service=psvc)
        versions = await engine.get_versions(project_id=42, entry_id=1)
        assert versions == []


class TestBaseEngineCount:
    """Test BaseMemoryEngine.count."""

    @pytest.mark.asyncio
    async def test_count_entries(self):
        psvc = _mock_psvc(count=5)
        engine = ProjectMemoryEngine(persistent_service=psvc)
        count = await engine.count(project_id=42)
        assert count == 5


class TestBaseEngineEnrich:
    """Test BaseMemoryEngine.enrich_response."""

    def test_enrich_extracts_domain_fields(self):
        entry = _make_response(
            category="project",
            metadata_json={"milestone": "MVP", "status": "active"},
        )
        engine = ProjectMemoryEngine()
        enriched = engine.enrich_response(entry)
        assert enriched["milestone"] == "MVP"
        assert enriched["status"] == "active"


# ── Domain-specific Engine Tests ────────────────────────────────────────────


class TestProjectMemoryEngine:
    """Test ProjectMemoryEngine domain methods."""

    @pytest.mark.asyncio
    async def test_get_by_phase(self):
        psvc = _mock_psvc(
            list=[
                _make_response(metadata_json={"project_phase": "design"}),
                _make_response(metadata_json={"project_phase": "build"}),
            ]
        )
        engine = ProjectMemoryEngine(persistent_service=psvc)
        results = await engine.get_by_phase(project_id=42, phase="design")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_by_milestone(self):
        psvc = _mock_psvc(
            list=[
                _make_response(metadata_json={"milestone": "MVP"}),
                _make_response(metadata_json={"milestone": "v2"}),
            ]
        )
        engine = ProjectMemoryEngine(persistent_service=psvc)
        results = await engine.get_by_milestone(project_id=42, milestone="MVP")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_project_timeline(self):
        psvc = _mock_psvc(
            list=[_make_response(metadata_json={"project_phase": "init"})]
        )
        engine = ProjectMemoryEngine(persistent_service=psvc)
        timeline = await engine.get_project_timeline(project_id=42)
        assert len(timeline) >= 1


class TestAgentMemoryEngine:
    """Test AgentMemoryEngine domain methods."""

    @pytest.mark.asyncio
    async def test_get_by_agent(self):
        psvc = _mock_psvc(
            list=[
                _make_response(agent_name="backend_developer"),
                _make_response(agent_name="frontend_developer"),
            ]
        )
        engine = AgentMemoryEngine(persistent_service=psvc)
        results = await engine.get_by_agent(
            project_id=42, agent_name="backend_developer",
        )
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_by_agent_type(self):
        psvc = _mock_psvc(
            list=[
                _make_response(metadata_json={"agent_type": "developer"}),
                _make_response(metadata_json={"agent_type": "reviewer"}),
            ]
        )
        engine = AgentMemoryEngine(persistent_service=psvc)
        results = await engine.get_by_agent_type(
            project_id=42, agent_type="developer",
        )
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_execution_stats(self):
        psvc = _mock_psvc(
            list=[
                _make_response(
                    agent_name="backend_developer",
                    metadata_json={"token_count": 1000, "execution_duration_ms": 500},
                ),
                _make_response(
                    agent_name="frontend_developer",
                    metadata_json={"token_count": 800, "execution_duration_ms": 300},
                ),
            ]
        )
        engine = AgentMemoryEngine(persistent_service=psvc)
        stats = await engine.get_execution_stats(project_id=42)
        assert stats["total_entries"] == 2
        assert stats["total_tokens"] == 1800
        assert stats["total_duration_ms"] == 800.0


class TestRequirementMemoryEngine:
    """Test RequirementMemoryEngine domain methods."""

    @pytest.mark.asyncio
    async def test_pre_create_defaults(self):
        engine = RequirementMemoryEngine()
        content, meta = engine._pre_create("test", {}, {})
        assert meta["priority"] == "medium"
        assert meta["status"] == "draft"

    @pytest.mark.asyncio
    async def test_get_by_priority(self):
        psvc = _mock_psvc(
            list=[
                _make_response(metadata_json={"priority": "high"}),
                _make_response(metadata_json={"priority": "low"}),
            ]
        )
        engine = RequirementMemoryEngine(persistent_service=psvc)
        results = await engine.get_by_priority(project_id=42, priority="high")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_requirements_summary(self):
        psvc = _mock_psvc(
            list=[
                _make_response(metadata_json={"priority": "high", "status": "approved"}),
                _make_response(metadata_json={"priority": "medium", "status": "draft"}),
            ]
        )
        engine = RequirementMemoryEngine(persistent_service=psvc)
        summary = await engine.get_requirements_summary(project_id=42)
        assert summary["total"] == 2
        assert summary["by_priority"]["high"] == 1


class TestArchitectureMemoryEngine:
    """Test ArchitectureMemoryEngine domain methods."""

    @pytest.mark.asyncio
    async def test_get_by_component(self):
        psvc = _mock_psvc(
            list=[
                _make_response(metadata_json={"component_name": "auth-service"}),
                _make_response(metadata_json={"component_name": "api-gateway"}),
            ]
        )
        engine = ArchitectureMemoryEngine(persistent_service=psvc)
        results = await engine.get_by_component(
            project_id=42, component_name="auth-service",
        )
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_by_layer(self):
        psvc = _mock_psvc(
            list=[
                _make_response(metadata_json={"layer": "presentation"}),
                _make_response(metadata_json={"layer": "data"}),
            ]
        )
        engine = ArchitectureMemoryEngine(persistent_service=psvc)
        results = await engine.get_by_layer(project_id=42, layer="data")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_architecture_summary(self):
        psvc = _mock_psvc(
            list=[
                _make_response(metadata_json={
                    "layer": "business",
                    "pattern": "repository",
                    "component_name": "user-svc",
                    "tech_stack": ["python", "fastapi"],
                }),
            ]
        )
        engine = ArchitectureMemoryEngine(persistent_service=psvc)
        summary = await engine.get_architecture_summary(project_id=42)
        assert summary["total"] == 1
        assert "python" in summary["tech_stack"]


class TestDatabaseMemoryEngine:
    """Test DatabaseMemoryEngine domain methods."""

    def test_pre_create_defaults(self):
        engine = DatabaseMemoryEngine()
        content, meta = engine._pre_create("test", {}, {})
        assert meta["migration_status"] == "pending"
        assert meta["db_engine"] == "postgresql"

    @pytest.mark.asyncio
    async def test_get_by_table(self):
        psvc = _mock_psvc(
            list=[
                _make_response(metadata_json={"table_name": "users"}),
                _make_response(metadata_json={"table_name": "projects"}),
            ]
        )
        engine = DatabaseMemoryEngine(persistent_service=psvc)
        results = await engine.get_by_table(project_id=42, table_name="users")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_schema_map(self):
        psvc = _mock_psvc(
            list=[
                _make_response(metadata_json={
                    "table_name": "users",
                    "relationships": ["projects"],
                    "indexes": ["idx_users_email"],
                    "migration_status": "applied",
                }),
            ]
        )
        engine = DatabaseMemoryEngine(persistent_service=psvc)
        schema_map = await engine.get_schema_map(project_id=42)
        assert "users" in schema_map["tables"]
        assert schema_map["by_migration_status"]["applied"] == 1


class TestAPIMemoryEngine:
    """Test APIMemoryEngine domain methods."""

    @pytest.mark.asyncio
    async def test_get_by_endpoint(self):
        psvc = _mock_psvc(
            list=[
                _make_response(metadata_json={"endpoint": "/api/users"}),
                _make_response(metadata_json={"endpoint": "/api/projects"}),
            ]
        )
        engine = APIMemoryEngine(persistent_service=psvc)
        results = await engine.get_by_endpoint(
            project_id=42, endpoint="/api/users",
        )
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_by_method(self):
        psvc = _mock_psvc(
            list=[
                _make_response(metadata_json={"method": "GET"}),
                _make_response(metadata_json={"method": "POST"}),
            ]
        )
        engine = APIMemoryEngine(persistent_service=psvc)
        results = await engine.get_by_method(project_id=42, method="get")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_api_catalog(self):
        psvc = _mock_psvc(
            list=[
                _make_response(metadata_json={
                    "endpoint": "/api/users",
                    "method": "GET",
                    "auth_required": True,
                    "api_version": "v1",
                }),
            ]
        )
        engine = APIMemoryEngine(persistent_service=psvc)
        catalog = await engine.get_api_catalog(project_id=42)
        assert catalog["total"] == 1
        assert "/api/users" in catalog["by_method"]["GET"]


class TestBackendMemoryEngine:
    """Test BackendMemoryEngine domain methods."""

    def test_pre_create_defaults(self):
        engine = BackendMemoryEngine()
        content, meta = engine._pre_create("test", {}, {})
        assert meta["language"] == "python"

    @pytest.mark.asyncio
    async def test_get_by_module(self):
        psvc = _mock_psvc(
            list=[
                _make_response(metadata_json={"module_name": "auth"}),
                _make_response(metadata_json={"module_name": "core"}),
            ]
        )
        engine = BackendMemoryEngine(persistent_service=psvc)
        results = await engine.get_by_module(project_id=42, module_name="auth")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_dependency_map(self):
        psvc = _mock_psvc(
            list=[
                _make_response(metadata_json={
                    "module_name": "api",
                    "dependencies": ["fastapi", "sqlalchemy"],
                    "code_type": "route",
                    "framework": "fastapi",
                }),
            ]
        )
        engine = BackendMemoryEngine(persistent_service=psvc)
        dep_map = await engine.get_dependency_map(project_id=42)
        assert "fastapi" in dep_map["dependencies"]


class TestFrontendMemoryEngine:
    """Test FrontendMemoryEngine domain methods."""

    @pytest.mark.asyncio
    async def test_get_by_component(self):
        psvc = _mock_psvc(
            list=[
                _make_response(metadata_json={"component_name": "Sidebar"}),
                _make_response(metadata_json={"component_name": "Header"}),
            ]
        )
        engine = FrontendMemoryEngine(persistent_service=psvc)
        results = await engine.get_by_component(
            project_id=42, component_name="Sidebar",
        )
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_component_tree(self):
        psvc = _mock_psvc(
            list=[
                _make_response(metadata_json={
                    "component_name": "LoginPage",
                    "component_type": "page",
                    "route_path": "/login",
                    "framework": "react",
                    "styling": "tailwind",
                }),
            ]
        )
        engine = FrontendMemoryEngine(persistent_service=psvc)
        tree = await engine.get_component_tree(project_id=42)
        assert tree["total"] == 1
        assert "/login" in tree["routes"]


class TestSecurityMemoryEngine:
    """Test SecurityMemoryEngine domain methods."""

    @pytest.mark.asyncio
    async def test_get_by_severity(self):
        psvc = _mock_psvc(
            list=[
                _make_response(metadata_json={"severity": "critical"}),
                _make_response(metadata_json={"severity": "low"}),
            ]
        )
        engine = SecurityMemoryEngine(persistent_service=psvc)
        results = await engine.get_by_severity(project_id=42, severity="critical")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_security_dashboard(self):
        psvc = _mock_psvc(
            list=[
                _make_response(metadata_json={
                    "severity": "high",
                    "scan_type": "sast",
                    "vulnerability_type": "XSS",
                    "affected_component": "frontend",
                    "compliance": ["owasp"],
                }),
            ]
        )
        engine = SecurityMemoryEngine(persistent_service=psvc)
        dashboard = await engine.get_security_dashboard(project_id=42)
        assert dashboard["total"] == 1
        assert dashboard["by_severity"]["high"] == 1


class TestTestingMemoryEngine:
    """Test TestingMemoryEngine domain methods."""

    @pytest.mark.asyncio
    async def test_get_by_test_type(self):
        psvc = _mock_psvc(
            list=[
                _make_response(metadata_json={"test_type": "unit"}),
                _make_response(metadata_json={"test_type": "integration"}),
            ]
        )
        engine = TestingMemoryEngine(persistent_service=psvc)
        results = await engine.get_by_test_type(project_id=42, test_type="unit")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_quality_report(self):
        psvc = _mock_psvc(
            list=[
                _make_response(metadata_json={
                    "test_type": "unit",
                    "coverage_percent": 85.0,
                    "pass_rate": 98.0,
                    "total_tests": 100,
                    "failed_tests": 2,
                    "skipped_tests": 5,
                }),
            ]
        )
        engine = TestingMemoryEngine(persistent_service=psvc)
        report = await engine.get_quality_report(project_id=42)
        assert report["total_entries"] == 1
        assert report["total_tests"] == 100
        assert report["avg_coverage_percent"] == 85.0


class TestDeploymentMemoryEngine:
    """Test DeploymentMemoryEngine domain methods."""

    @pytest.mark.asyncio
    async def test_get_by_environment(self):
        psvc = _mock_psvc(
            list=[
                _make_response(metadata_json={"environment": "production"}),
                _make_response(metadata_json={"environment": "staging"}),
            ]
        )
        engine = DeploymentMemoryEngine(persistent_service=psvc)
        results = await engine.get_by_environment(
            project_id=42, environment="production",
        )
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_by_provider(self):
        psvc = _mock_psvc(
            list=[
                _make_response(metadata_json={"provider": "render"}),
                _make_response(metadata_json={"provider": "vercel"}),
            ]
        )
        engine = DeploymentMemoryEngine(persistent_service=psvc)
        results = await engine.get_by_provider(project_id=42, provider="render")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_deployment_overview(self):
        psvc = _mock_psvc(
            list=[
                _make_response(metadata_json={
                    "environment": "production",
                    "provider": "render",
                    "status": "deployed",
                    "deploy_url": "https://app.render.com",
                    "env_variables": ["DATABASE_URL", "JWT_SECRET"],
                }),
            ]
        )
        engine = DeploymentMemoryEngine(persistent_service=psvc)
        overview = await engine.get_deployment_overview(project_id=42)
        assert overview["total"] == 1
        assert "DATABASE_URL" in overview["required_env_variables"]


class TestDocumentationMemoryEngine:
    """Test DocumentationMemoryEngine domain methods."""

    @pytest.mark.asyncio
    async def test_get_by_doc_type(self):
        psvc = _mock_psvc(
            list=[
                _make_response(metadata_json={"doc_type": "readme"}),
                _make_response(metadata_json={"doc_type": "api-docs"}),
            ]
        )
        engine = DocumentationMemoryEngine(persistent_service=psvc)
        results = await engine.get_by_doc_type(project_id=42, doc_type="readme")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_documentation_index(self):
        psvc = _mock_psvc(
            list=[
                _make_response(metadata_json={
                    "doc_type": "readme",
                    "audience": "developer",
                    "doc_format": "markdown",
                    "auto_generated": True,
                    "related_files": ["README.md"],
                }),
            ]
        )
        engine = DocumentationMemoryEngine(persistent_service=psvc)
        index = await engine.get_documentation_index(project_id=42)
        assert index["total"] == 1
        assert index["auto_generated_count"] == 1
