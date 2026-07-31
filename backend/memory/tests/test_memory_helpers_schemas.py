"""
Tests for Phase 5.1 — Memory Helpers & Schemas

Unit tests for utility functions and all 12 domain-specific Pydantic
schemas.  No database or network required.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from typing import Any, Dict

from memory.utils.memory_helpers import (
    inject_domain_fields,
    extract_domain_fields,
    merge_metadata,
    sanitize_content,
    validate_domain,
    build_search_metadata,
    format_memory_response,
    VALID_DOMAINS,
)
from memory.persistent_schemas import MemoryCategory


# ===========================================================================
# Memory Helpers Tests
# ===========================================================================


class TestInjectDomainFields:

    def test_injects_non_none_values(self):
        meta = {"existing": "value"}
        fields = {"new_field": "test", "empty": None}
        result = inject_domain_fields(meta, fields)
        assert result["new_field"] == "test"
        assert "empty" not in result
        assert result["existing"] == "value"

    def test_preserves_existing_keys(self):
        meta = {"key": "original"}
        fields = {"other": "new"}
        result = inject_domain_fields(meta, fields)
        assert result["key"] == "original"
        assert result["other"] == "new"

    def test_overwrites_existing_keys_with_non_none(self):
        meta = {"key": "original"}
        fields = {"key": "overwritten"}
        result = inject_domain_fields(meta, fields)
        assert result["key"] == "overwritten"

    def test_empty_fields(self):
        meta = {"key": "value"}
        result = inject_domain_fields(meta, {})
        assert result == {"key": "value"}


class TestExtractDomainFields:

    def test_extracts_existing_keys(self):
        meta = {"priority": "high", "status": "active", "extra": "data"}
        result = extract_domain_fields(meta, ["priority", "status"])
        assert result == {"priority": "high", "status": "active"}

    def test_skips_missing_keys(self):
        meta = {"priority": "high"}
        result = extract_domain_fields(meta, ["priority", "missing"])
        assert result == {"priority": "high"}

    def test_empty_metadata(self):
        result = extract_domain_fields({}, ["key1", "key2"])
        assert result == {}


class TestMergeMetadata:

    def test_basic_merge(self):
        existing = {"a": 1, "b": 2}
        updates = {"b": 3, "c": 4}
        result = merge_metadata(existing, updates)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_none_removes_key(self):
        existing = {"a": 1, "b": 2}
        updates = {"b": None}
        result = merge_metadata(existing, updates)
        assert result == {"a": 1}

    def test_nested_merge(self):
        existing = {"nested": {"x": 1, "y": 2}}
        updates = {"nested": {"y": 3, "z": 4}}
        result = merge_metadata(existing, updates)
        assert result == {"nested": {"x": 1, "y": 3, "z": 4}}

    def test_none_updates_returns_copy(self):
        existing = {"a": 1}
        result = merge_metadata(existing, None)
        assert result == {"a": 1}
        assert result is not existing


class TestSanitizeContent:

    def test_strips_control_characters(self):
        content = "Hello\x00World\x07"
        result = sanitize_content(content)
        assert "\x00" not in result
        assert "\x07" not in result

    def test_preserves_newlines_and_tabs(self):
        content = "Line 1\nLine 2\tTabbed"
        result = sanitize_content(content)
        assert "\n" in result
        assert "\t" in result

    def test_escapes_html(self):
        content = "<script>alert('xss')</script>"
        result = sanitize_content(content)
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_trims_whitespace(self):
        content = "   Hello   "
        result = sanitize_content(content)
        assert result == "Hello"


class TestValidateDomain:

    def test_valid_domains(self):
        for domain in VALID_DOMAINS:
            cat = validate_domain(domain)
            assert isinstance(cat, MemoryCategory)

    def test_case_insensitive(self):
        cat = validate_domain("PROJECT")
        assert cat == MemoryCategory.PROJECT

    def test_invalid_domain(self):
        with pytest.raises(ValueError, match="Unknown memory domain"):
            validate_domain("nonexistent")


class TestBuildSearchMetadata:

    def test_basic_filter(self):
        result = build_search_metadata(project_id=42)
        assert result == {"project_id": 42}

    def test_with_category_and_agent(self):
        result = build_search_metadata(
            project_id=42, category="security", agent_name="tester",
        )
        assert result["category"] == "security"
        assert result["agent_name"] == "tester"


class TestFormatMemoryResponse:

    def test_extracts_domain_fields_into_response(self):
        data = {
            "id": 1,
            "metadata_json": {"priority": "high", "status": "approved"},
        }
        result = format_memory_response(data, ["priority", "status"])
        assert result["priority"] == "high"
        assert result["status"] == "approved"


# ===========================================================================
# Domain Schema Tests
# ===========================================================================


class TestDomainSchemas:
    """Validate all 12 domain schema Create/Update/Response/SearchResult."""

    def test_project_schemas(self):
        from memory.schemas.project import (
            ProjectMemoryCreate, ProjectMemoryUpdate,
            ProjectMemoryResponse, ProjectMemorySearchResult,
        )
        body = ProjectMemoryCreate(content="Test project", milestone="MVP")
        assert body.content == "Test project"
        assert body.milestone == "MVP"

        update = ProjectMemoryUpdate(content="Updated", project_phase="design")
        assert update.project_phase == "design"

    def test_agent_schemas(self):
        from memory.schemas.agent import AgentMemoryCreate, AgentMemoryResponse
        body = AgentMemoryCreate(
            content="Agent output", agent_name="backend_developer",
            model_used="llama-3.1-70b", token_count=1000,
        )
        assert body.agent_name == "backend_developer"
        assert body.token_count == 1000

    def test_requirement_schemas(self):
        from memory.schemas.requirement import RequirementMemoryCreate
        body = RequirementMemoryCreate(
            content="Auth requirement", priority="high",
            acceptance_criteria=["Must support JWT"],
        )
        assert body.priority == "high"
        assert len(body.acceptance_criteria) == 1

    def test_architecture_schemas(self):
        from memory.schemas.architecture import ArchitectureMemoryCreate
        body = ArchitectureMemoryCreate(
            content="Architecture decision",
            component_name="auth-service",
            pattern="repository",
            tech_stack=["python", "fastapi"],
        )
        assert body.component_name == "auth-service"

    def test_database_schemas(self):
        from memory.schemas.database import DatabaseMemoryCreate
        body = DatabaseMemoryCreate(
            content="Table schema",
            table_name="users",
            indexes=["idx_email"],
        )
        assert body.table_name == "users"

    def test_api_schemas(self):
        from memory.schemas.api import APIMemoryCreate
        body = APIMemoryCreate(
            content="GET /api/users",
            endpoint="/api/users",
            method="GET",
            auth_required=True,
        )
        assert body.auth_required is True

    def test_backend_schemas(self):
        from memory.schemas.backend import BackendMemoryCreate
        body = BackendMemoryCreate(
            content="def foo(): pass",
            language="python",
            code_type="service",
        )
        assert body.language == "python"

    def test_frontend_schemas(self):
        from memory.schemas.frontend import FrontendMemoryCreate
        body = FrontendMemoryCreate(
            content="<Component />",
            component_name="LoginForm",
            framework="react",
        )
        assert body.framework == "react"

    def test_security_schemas(self):
        from memory.schemas.security import SecurityMemoryCreate
        body = SecurityMemoryCreate(
            content="XSS vulnerability",
            severity="high",
            cwe_id="CWE-79",
            compliance=["owasp"],
        )
        assert body.cwe_id == "CWE-79"

    def test_testing_schemas(self):
        from memory.schemas.testing import TestingMemoryCreate
        body = TestingMemoryCreate(
            content="Unit test results",
            test_type="unit",
            coverage_percent=95.0,
            total_tests=200,
        )
        assert body.coverage_percent == 95.0

    def test_deployment_schemas(self):
        from memory.schemas.deployment import DeploymentMemoryCreate
        body = DeploymentMemoryCreate(
            content="Render config",
            environment="production",
            provider="render",
            env_variables=["DATABASE_URL"],
        )
        assert body.provider == "render"

    def test_documentation_schemas(self):
        from memory.schemas.documentation import DocumentationMemoryCreate
        body = DocumentationMemoryCreate(
            content="# README",
            doc_type="readme",
            doc_format="markdown",
            auto_generated=True,
        )
        assert body.auto_generated is True


class TestSchemaPackageImports:
    """Verify all 48 schema classes are importable from the package."""

    def test_all_schemas_importable(self):
        from memory.schemas import (
            ProjectMemoryCreate, ProjectMemoryUpdate,
            ProjectMemoryResponse, ProjectMemorySearchResult,
            AgentMemoryCreate, AgentMemoryUpdate,
            AgentMemoryResponse, AgentMemorySearchResult,
            RequirementMemoryCreate, RequirementMemoryUpdate,
            RequirementMemoryResponse, RequirementMemorySearchResult,
            ArchitectureMemoryCreate, ArchitectureMemoryUpdate,
            ArchitectureMemoryResponse, ArchitectureMemorySearchResult,
            DatabaseMemoryCreate, DatabaseMemoryUpdate,
            DatabaseMemoryResponse, DatabaseMemorySearchResult,
            APIMemoryCreate, APIMemoryUpdate,
            APIMemoryResponse, APIMemorySearchResult,
            BackendMemoryCreate, BackendMemoryUpdate,
            BackendMemoryResponse, BackendMemorySearchResult,
            FrontendMemoryCreate, FrontendMemoryUpdate,
            FrontendMemoryResponse, FrontendMemorySearchResult,
            SecurityMemoryCreate, SecurityMemoryUpdate,
            SecurityMemoryResponse, SecurityMemorySearchResult,
            TestingMemoryCreate, TestingMemoryUpdate,
            TestingMemoryResponse, TestingMemorySearchResult,
            DeploymentMemoryCreate, DeploymentMemoryUpdate,
            DeploymentMemoryResponse, DeploymentMemorySearchResult,
            DocumentationMemoryCreate, DocumentationMemoryUpdate,
            DocumentationMemoryResponse, DocumentationMemorySearchResult,
        )
        # If we get here, all imports succeeded
        assert True
