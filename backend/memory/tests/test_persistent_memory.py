"""
Tests for Phase 5.1 — Persistent Project Memory Engine

Schema tests  — no DB required.
Service tests — mocked AsyncSessionLocal.
Router tests  — TestClient with mocked service dependency.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from memory.persistent_schemas import (
    MemoryCategory,
    PersistentMemoryCreate,
    PersistentMemoryUpdate,
    PersistentMemoryResponse,
    PersistentMemoryVersionResponse,
    PersistentMemorySearchRequest,
    PersistentMemoryListResponse,
    PersistentMemorySearchResponse,
    PersistentMemorySummaryResponse,
    PersistentMemoryDeleteResponse,
    CategorySummary,
)
from memory.persistent_models import PersistentProjectMemory, PersistentMemoryVersion
from memory.persistent_service import PersistentMemoryService


# ===========================================================================
# Schema Tests
# ===========================================================================

class TestPersistentMemorySchemas:
    """Test all Phase 5.1 Pydantic schemas."""

    def test_memory_category_enum_values(self):
        assert MemoryCategory.PROJECT.value == "project"
        assert MemoryCategory.AGENT.value == "agent"
        assert MemoryCategory.REQUIREMENT.value == "requirement"
        assert MemoryCategory.ARCHITECTURE.value == "architecture"
        assert MemoryCategory.DATABASE.value == "database"
        assert MemoryCategory.API.value == "api"
        assert MemoryCategory.BACKEND.value == "backend"
        assert MemoryCategory.FRONTEND.value == "frontend"
        assert MemoryCategory.SECURITY.value == "security"
        assert MemoryCategory.TESTING.value == "testing"
        assert MemoryCategory.DEPLOYMENT.value == "deployment"
        assert MemoryCategory.DOCUMENTATION.value == "documentation"
        assert MemoryCategory.GENERATED_FILE.value == "generated_file"
        assert MemoryCategory.EXPORT.value == "export"
        assert len(list(MemoryCategory)) == 14

    def test_persistent_memory_create(self):
        body = PersistentMemoryCreate(
            category=MemoryCategory.REQUIREMENT,
            content="Test requirement",
            agent_name="project_manager",
            metadata_json={"priority": "high"},
            version=1,
        )
        assert body.category == MemoryCategory.REQUIREMENT
        assert body.content == "Test requirement"
        assert body.agent_name == "project_manager"
        assert body.metadata_json == {"priority": "high"}
        assert body.version == 1

    def test_persistent_memory_create_defaults(self):
        body = PersistentMemoryCreate(
            category=MemoryCategory.SECURITY,
            content="Security analysis result",
        )
        assert body.agent_name == "system"
        assert body.metadata_json == {}
        assert body.version == 1

    def test_persistent_memory_update(self):
        body = PersistentMemoryUpdate(
            content="Updated content",
            metadata_json={"status": "reviewed"},
            change_reason="Code review feedback",
            changed_by="qa_engineer",
        )
        assert body.content == "Updated content"
        assert body.metadata_json == {"status": "reviewed"}
        assert body.change_reason == "Code review feedback"
        assert body.changed_by == "qa_engineer"

    def test_persistent_memory_update_defaults(self):
        body = PersistentMemoryUpdate(content="Updated content")
        assert body.change_reason == ""
        assert body.changed_by == "system"

    def test_persistent_memory_response_from_attributes(self):
        now = datetime.now(timezone.utc)
        data = {
            "id": 1,
            "project_id": 42,
            "category": "architecture",
            "agent_name": "solution_architect",
            "content": "System architecture document",
            "metadata_json": {"version": "1.0"},
            "version": 1,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        resp = PersistentMemoryResponse.model_validate(data)
        assert resp.id == 1
        assert resp.project_id == 42
        assert resp.category == "architecture"
        assert resp.agent_name == "solution_architect"

    def test_category_summary(self):
        now = datetime.now(timezone.utc)
        summary = CategorySummary(
            category="testing",
            count=5,
            latest_version=3,
            last_updated=now,
        )
        assert summary.category == "testing"
        assert summary.count == 5
        assert summary.latest_version == 3

    def test_search_request(self):
        req = PersistentMemorySearchRequest(query="authentication", category=MemoryCategory.SECURITY)
        assert req.query == "authentication"
        assert req.category == MemoryCategory.SECURITY

    def test_search_request_no_category(self):
        req = PersistentMemorySearchRequest(query="database")
        assert req.query == "database"
        assert req.category is None

    def test_delete_response(self):
        resp = PersistentMemoryDeleteResponse(message="Deleted", entry_id=5)
        assert resp.message == "Deleted"
        assert resp.entry_id == 5

    def test_persistent_memory_version_response(self):
        now = datetime.now(timezone.utc)
        data = {
            "id": 10,
            "entry_id": 1,
            "project_id": 42,
            "category": "backend",
            "content": "v2 content",
            "metadata_json": {"diff": "small"},
            "version": 2,
            "change_reason": "Refactored",
            "changed_by": "backend_developer",
            "created_at": now,
        }
        resp = PersistentMemoryVersionResponse.model_validate(data)
        assert resp.entry_id == 1
        assert resp.version == 2
        assert resp.change_reason == "Refactored"

    def test_list_response(self):
        now = datetime.now(timezone.utc)
        entry_data = {
            "id": 1, "project_id": 42, "category": "api", "agent_name": "api_designer",
            "content": "API contract", "metadata_json": {}, "version": 1,
            "is_active": True, "created_at": now, "updated_at": now,
        }
        entry = PersistentMemoryResponse.model_validate(entry_data)
        resp = PersistentMemoryListResponse(
            project_id=42,
            category="api",
            entries=[entry],
            total=1,
        )
        assert resp.total == 1
        assert resp.entries[0].content == "API contract"

    def test_summary_response(self):
        now = datetime.now(timezone.utc)
        cat = CategorySummary(category="requirements", count=3, latest_version=2, last_updated=now)
        resp = PersistentMemorySummaryResponse(
            project_id=42,
            categories=[cat],
            total_entries=3,
        )
        assert resp.total_entries == 3
        assert resp.categories[0].category == "requirements"


# ===========================================================================
# Service Tests (mocked DB)
# ===========================================================================

class TestPersistentMemoryService:
    """Test PersistentMemoryService with mocked AsyncSessionLocal."""

    @pytest.mark.asyncio
    async def test_create_entry(self):
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session

        with patch("memory.persistent_service.AsyncSessionLocal", return_value=mock_session):
            from memory.persistent_service import PersistentMemoryService
            from memory.persistent_schemas import MemoryCategory

            from memory.persistent_models import PersistentProjectMemory
            real_entry = PersistentProjectMemory(
                project_id=42,
                category="requirement",
                agent_name="project_manager",
                content="Test requirement",
                metadata_json={},
                version=1,
            )
            real_entry.id = 1

            mock_session.add = MagicMock()
            mock_session.flush = AsyncMock()
            mock_session.commit = AsyncMock()

            async def refresh_side_effect(inst):
                inst.id = 1
                inst.created_at = datetime.now(timezone.utc)
                inst.updated_at = datetime.now(timezone.utc)
                inst.is_active = True
            mock_session.refresh = AsyncMock(side_effect=refresh_side_effect)

            svc = PersistentMemoryService()
            result = await svc.create_entry(
                project_id=42,
                category=MemoryCategory.REQUIREMENT,
                content="Test requirement",
                agent_name="project_manager",
            )
            assert result is not None
            assert result.project_id == 42

    @pytest.mark.asyncio
    async def test_get_entry_found(self):
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session

        with patch("memory.persistent_service.AsyncSessionLocal", return_value=mock_session):
            from memory.persistent_service import PersistentMemoryService
            svc = PersistentMemoryService()

            mock_entry = MagicMock(spec=PersistentProjectMemory)
            mock_entry.id = 1
            mock_entry.project_id = 42
            mock_entry.category = "backend"
            mock_entry.agent_name = "backend_developer"
            mock_entry.content = "def main(): pass"
            mock_entry.metadata_json = {}
            mock_entry.version = 1
            mock_entry.is_active = True
            mock_entry.created_at = datetime.now(timezone.utc)
            mock_entry.updated_at = datetime.now(timezone.utc)

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_entry
            mock_session.execute = AsyncMock(return_value=mock_result)

            result = await svc.get_entry(project_id=42, entry_id=1)
            assert result is not None
            assert result.content == "def main(): pass"

    @pytest.mark.asyncio
    async def test_get_entry_not_found(self):
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session

        with patch("memory.persistent_service.AsyncSessionLocal", return_value=mock_session):
            from memory.persistent_service import PersistentMemoryService
            svc = PersistentMemoryService()

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session.execute = AsyncMock(return_value=mock_result)

            result = await svc.get_entry(project_id=42, entry_id=999)
            assert result is None

    @pytest.mark.asyncio
    async def test_delete_entry_found(self):
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session

        with patch("memory.persistent_service.AsyncSessionLocal", return_value=mock_session):
            from memory.persistent_service import PersistentMemoryService
            svc = PersistentMemoryService()

            mock_entry = MagicMock(spec=PersistentProjectMemory)
            mock_entry.id = 1
            mock_entry.project_id = 42
            mock_entry.is_active = True

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_entry
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.commit = AsyncMock()

            result = await svc.delete_entry(project_id=42, entry_id=1)
            assert result is True
            assert mock_entry.is_active is False

    @pytest.mark.asyncio
    async def test_delete_entry_not_found(self):
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session

        with patch("memory.persistent_service.AsyncSessionLocal", return_value=mock_session):
            from memory.persistent_service import PersistentMemoryService
            svc = PersistentMemoryService()

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session.execute = AsyncMock(return_value=mock_result)

            result = await svc.delete_entry(project_id=42, entry_id=999)
            assert result is False

    @pytest.mark.asyncio
    async def test_search_entries(self):
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session

        with patch("memory.persistent_service.AsyncSessionLocal", return_value=mock_session):
            from memory.persistent_service import PersistentMemoryService
            svc = PersistentMemoryService()

            mock_entry = MagicMock(spec=PersistentProjectMemory)
            mock_entry.id = 1
            mock_entry.project_id = 42
            mock_entry.category = "security"
            mock_entry.agent_name = "security_engineer"
            mock_entry.content = "JWT authentication analysis"
            mock_entry.metadata_json = {}
            mock_entry.version = 1
            mock_entry.is_active = True
            mock_entry.created_at = datetime.now(timezone.utc)
            mock_entry.updated_at = datetime.now(timezone.utc)

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_entry]
            mock_session.execute = AsyncMock(return_value=mock_result)

            results = await svc.search_entries(project_id=42, query="authentication")
            assert len(results) == 1
            assert results[0].content == "JWT authentication analysis"

    @pytest.mark.asyncio
    async def test_count_entries(self):
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session

        with patch("memory.persistent_service.AsyncSessionLocal", return_value=mock_session):
            from memory.persistent_service import PersistentMemoryService
            svc = PersistentMemoryService()

            mock_result = MagicMock()
            mock_result.scalar.return_value = 5
            mock_session.execute = AsyncMock(return_value=mock_result)

            count = await svc.count_entries(project_id=42)
            assert count == 5


# ===========================================================================
# Router Tests
# ===========================================================================

class TestPersistentMemoryRouter:
    """Test FastAPI router with mocked service dependency."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        app = FastAPI()
        from memory.routers.persistent_memory import router
        app.include_router(router)
        return TestClient(app)

    def test_create_entry_requires_auth(self, client):
        resp = client.post(
            "/pmemory/projects/1/entries",
            json={"category": "requirement", "content": "Test"},
        )
        assert resp.status_code == 403 or resp.status_code == 401

    def test_list_entries_requires_auth(self, client):
        resp = client.get("/pmemory/projects/1/entries")
        assert resp.status_code == 403 or resp.status_code == 401

    def test_get_entry_requires_auth(self, client):
        resp = client.get("/pmemory/projects/1/entries/1")
        assert resp.status_code == 403 or resp.status_code == 401

    def test_update_entry_requires_auth(self, client):
        resp = client.put(
            "/pmemory/projects/1/entries/1",
            json={"content": "Updated"},
        )
        assert resp.status_code == 403 or resp.status_code == 401

    def test_delete_entry_requires_auth(self, client):
        resp = client.delete("/pmemory/projects/1/entries/1")
        assert resp.status_code == 403 or resp.status_code == 401

    def test_search_requires_auth(self, client):
        resp = client.post(
            "/pmemory/projects/1/entries/search",
            json={"query": "test"},
        )
        assert resp.status_code == 403 or resp.status_code == 401

    def test_versions_requires_auth(self, client):
        resp = client.get("/pmemory/projects/1/entries/1/versions")
        assert resp.status_code == 403 or resp.status_code == 401

    def test_category_summary_requires_auth(self, client):
        resp = client.get("/pmemory/projects/1/categories/summary")
        assert resp.status_code == 403 or resp.status_code == 401


# ===========================================================================
# Integration Tests (SQLite-backed)
# ===========================================================================

class TestPersistentMemoryIntegration:
    """Real DB tests using SQLite. Requires aiosqlite."""

    @pytest.fixture(autouse=True)
    async def setup_db(self):
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from app.db import Base
        from memory.persistent_models import PersistentProjectMemory, PersistentMemoryVersion

        self.engine = create_async_engine("sqlite+aiosqlite://", echo=False)
        self.TestSessionLocal = async_sessionmaker(self.engine, expire_on_commit=False)

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await self.engine.dispose()

    async def _entry(self, svc, project_id=100, category=None, content="Test", agent="test", **kw):
        async with self.TestSessionLocal() as session:
            return await svc.create_entry(
                project_id=project_id,
                category=category or MemoryCategory.REQUIREMENT,
                content=content,
                agent_name=agent,
                session=session,
                **kw,
            )

    @pytest.mark.asyncio
    async def test_full_crud_lifecycle(self):
        svc = PersistentMemoryService()

        async with self.TestSessionLocal() as session:
            entry = await svc.create_entry(
                project_id=100, category=MemoryCategory.REQUIREMENT,
                content="Initial requirement", agent_name="pm",
                session=session,
            )
            assert entry.id > 0
            assert entry.project_id == 100
            assert entry.category == "requirement"
            assert entry.version == 1

            # Read
            fetched = await svc.get_entry(project_id=100, entry_id=entry.id, session=session)
            assert fetched is not None
            assert fetched.content == "Initial requirement"

            # Update
            updated = await svc.update_entry(
                project_id=100, entry_id=entry.id,
                content="Updated requirement",
                change_reason="Sprint review", changed_by="po",
                session=session,
            )
            assert updated is not None
            assert updated.version == 2
            assert updated.content == "Updated requirement"

            # Version history
            versions = await svc.get_version_history(
                project_id=100, entry_id=entry.id, session=session,
            )
            assert len(versions) == 2
            assert versions[0].version == 2
            assert versions[1].version == 1

            # Search
            results = await svc.search_entries(
                project_id=100, query="requirement", session=session,
            )
            assert len(results) >= 1

            # List
            all_entries = await svc.list_entries(project_id=100, session=session)
            assert len(all_entries) >= 1

            # Count
            count = await svc.count_entries(project_id=100, session=session)
            assert count >= 1

            # Summary
            summaries = await svc.get_category_summary(project_id=100, session=session)
            assert any(s.category == "requirement" for s in summaries)

            # Delete
            deleted = await svc.delete_entry(project_id=100, entry_id=entry.id, session=session)
            assert deleted is True

            # Verify deleted
            after_delete = await svc.get_entry(project_id=100, entry_id=entry.id, session=session)
            assert after_delete is None

    @pytest.mark.asyncio
    async def test_multiple_categories(self):
        svc = PersistentMemoryService()
        categories = [
            MemoryCategory.ARCHITECTURE,
            MemoryCategory.DATABASE,
            MemoryCategory.API,
            MemoryCategory.SECURITY,
            MemoryCategory.TESTING,
        ]
        async with self.TestSessionLocal() as session:
            for cat in categories:
                await svc.create_entry(
                    project_id=200, category=cat,
                    content=f"Content for {cat.value}", session=session,
                )

            summary = await svc.get_category_summary(project_id=200, session=session)
            assert len(summary) == 5

            count = await svc.count_entries(project_id=200, session=session)
            assert count == 5

    @pytest.mark.asyncio
    async def test_search_by_agent_name(self):
        svc = PersistentMemoryService()
        async with self.TestSessionLocal() as session:
            await svc.create_entry(
                project_id=300, category=MemoryCategory.BACKEND,
                content="def handle(): pass", agent_name="backend_dev",
                session=session,
            )
            results = await svc.search_entries(
                project_id=300, query="backend_dev", session=session,
            )
            assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_category_filtered_list(self):
        svc = PersistentMemoryService()
        async with self.TestSessionLocal() as session:
            for cat in [MemoryCategory.FRONTEND, MemoryCategory.DEPLOYMENT]:
                await svc.create_entry(project_id=400, category=cat, content=cat.value, session=session)

            frontend = await svc.list_entries(
                project_id=400, category=MemoryCategory.FRONTEND, session=session,
            )
            assert len(frontend) == 1
            assert frontend[0].category == "frontend"
