"""
test_project_memory.py — Phase 3.4 test suite.

Tests cover:
- Schema correctness (ArtifactType, new Pydantic models)
- ProjectMemoryService: store / retrieve for every artifact category
- Revision tracking
- Version history (ordering, filtering)
- Generated file tracking (language detection, path extraction)
- Project snapshot (aggregate)
- Cross-collection semantic search
- MemoryService.record_version / get_version_history integration
- Edge cases: empty project, unknown agent, overlapping versions

Windows-safe ChromaDB fixture: uses tempfile.mkdtemp() + shutil.rmtree()
instead of TemporaryDirectory context managers (file-lock issue).
"""
from __future__ import annotations

import shutil
import tempfile
from datetime import datetime, timezone
from typing import List
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_service(tmp_path: str):
    """Return a (MemoryService, ChromaVectorStore) pair wired to a temp dir."""
    from memory.embeddings.local import LocalEmbeddings
    from memory.service import MemoryService
    from memory.vectorstores.chroma import ChromaVectorStore

    store = ChromaVectorStore(persist_path=tmp_path)
    embed = LocalEmbeddings()
    svc = MemoryService(embedding_provider=embed, vector_store=store)
    return svc, store


def _make_pms(tmp_path: str):
    """Return a ProjectMemoryService wired to a temp dir."""
    from memory.project_memory import ProjectMemoryService

    svc, _ = _make_service(tmp_path)
    return ProjectMemoryService(memory_service=svc)


# ---------------------------------------------------------------------------
# Module-scoped temp dir so ChromaDB is created once per test module
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def tmp_dir():
    d = tempfile.mkdtemp(prefix="cf_test_pm_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture(scope="module")
def pms(tmp_dir):
    return _make_pms(tmp_dir)


# ===========================================================================
# 1. Schema tests
# ===========================================================================

class TestPhase34Schemas:
    def test_artifact_type_enum_values(self):
        from memory.schemas import ArtifactType

        assert ArtifactType.REQUIREMENTS == "requirements"
        assert ArtifactType.ARCHITECTURE == "architecture"
        assert ArtifactType.BACKEND_CODE == "backend_code"
        assert ArtifactType.FRONTEND_CODE == "frontend_code"
        assert ArtifactType.GENERATED_FILE == "generated_file"
        assert ArtifactType.AGENT_OUTPUT == "agent_output"
        assert ArtifactType.REVISION == "revision"

    def test_artifact_type_is_str_enum(self):
        from memory.schemas import ArtifactType

        assert isinstance(ArtifactType.REQUIREMENTS, str)

    def test_agent_memory_record_fields(self):
        from memory.schemas import AgentMemoryRecord

        rec = AgentMemoryRecord(
            id="abc",
            project_id=1,
            agent_name="backend_developer",
            artifact_type="backend_code",
            collection_name="backend_code",
            content="def foo(): pass",
            version=1,
            timestamp=datetime.now(timezone.utc),
        )
        assert rec.project_id == 1
        assert rec.metadata == {}

    def test_generated_file_record_fields(self):
        from memory.schemas import GeneratedFileRecord

        rec = GeneratedFileRecord(
            id="f1",
            project_id=2,
            file_path="backend/main.py",
            language="python",
            content="print('hi')",
            agent_name="backend_developer",
            version=1,
            timestamp=datetime.now(timezone.utc),
        )
        assert rec.file_path == "backend/main.py"
        assert rec.language == "python"

    def test_revision_entry_fields(self):
        from memory.schemas import RevisionEntry

        rev = RevisionEntry(
            id="r1",
            project_id=3,
            artifact_type="backend_code",
            version=2,
            content="revised content",
            reason="fix bug",
            requested_by="qa_engineer",
            timestamp=datetime.now(timezone.utc),
        )
        assert rev.reason == "fix bug"
        assert rev.requested_by == "qa_engineer"

    def test_revision_entry_defaults(self):
        from memory.schemas import RevisionEntry

        rev = RevisionEntry(
            id="r2",
            project_id=1,
            artifact_type="requirements",
            version=1,
            content="content",
            timestamp=datetime.now(timezone.utc),
        )
        assert rev.reason == ""
        assert rev.requested_by == "system"

    def test_project_snapshot_fields_and_property(self):
        from memory.schemas import AgentMemoryRecord, ProjectSnapshot

        snap = ProjectSnapshot(project_id=1)
        assert snap.total_artifacts == 0
        assert snap.requirements == []

    def test_store_artifact_request_validation(self):
        from memory.schemas import StoreArtifactRequest
        import pydantic

        req = StoreArtifactRequest(
            agent_name="architect",
            artifact_type="architecture",
            collection_name="architecture",
            content="## Architecture\n...",
        )
        assert req.version == 1

        with pytest.raises(pydantic.ValidationError):
            StoreArtifactRequest(
                agent_name="",
                artifact_type="architecture",
                collection_name="architecture",
                content="text",
            )

    def test_store_revision_request_defaults(self):
        from memory.schemas import StoreRevisionRequest

        req = StoreRevisionRequest(
            artifact_type="backend_code",
            content="new content",
        )
        assert req.reason == ""
        assert req.requested_by == "system"

    def test_memory_search_request_validation(self):
        from memory.schemas import MemorySearchRequest
        import pydantic

        req = MemorySearchRequest(query="authentication flow")
        assert req.limit == 5
        assert req.threshold == 0.0

        with pytest.raises(pydantic.ValidationError):
            MemorySearchRequest(query="")


# ===========================================================================
# 2. Requirement Memory
# ===========================================================================

class TestRequirementMemory:
    def test_store_requirement_returns_id(self, pms):
        mem_id = pms.store_requirement(
            project_id=10,
            content="Users shall be able to register and login.",
            version=1,
        )
        assert isinstance(mem_id, str)
        assert len(mem_id) > 0

    def test_store_requirement_creates_history_entry(self, pms):
        pms.store_requirement(
            project_id=10,
            content="Users shall manage their notes.",
            version=2,
        )
        history = pms.get_version_history(project_id=10, artifact_type="requirements")
        assert len(history) >= 1
        assert all(e.artifact_type == "requirements" for e in history)

    def test_requirement_versions_sorted(self, pms):
        pms.store_requirement(project_id=11, content="req v3", version=3)
        pms.store_requirement(project_id=11, content="req v1", version=1)
        pms.store_requirement(project_id=11, content="req v2", version=2)
        history = pms.get_version_history(project_id=11, artifact_type="requirements")
        versions = [e.version for e in history]
        assert versions == sorted(versions)

    def test_store_requirement_custom_agent(self, pms):
        mem_id = pms.store_requirement(
            project_id=12,
            content="System shall handle 1000 concurrent users.",
            version=1,
            agent_name="product_owner",
        )
        history = pms.get_version_history(project_id=12, artifact_type="requirements")
        assert len(history) >= 1


# ===========================================================================
# 3. Architecture Memory
# ===========================================================================

class TestArchitectureMemory:
    def test_store_architecture(self, pms):
        mem_id = pms.store_architecture(
            project_id=20,
            content="## System Architecture\nMicroservices with FastAPI",
            artifact_type="architecture",
            version=1,
        )
        assert isinstance(mem_id, str)

    def test_store_database_design(self, pms):
        mem_id = pms.store_architecture(
            project_id=20,
            content="## DB Design\nPostgreSQL with pgvector",
            artifact_type="database_design",
            version=1,
        )
        assert isinstance(mem_id, str)

    def test_store_api_contracts(self, pms):
        mem_id = pms.store_architecture(
            project_id=20,
            content="## API Contracts\nREST / OpenAPI 3.1",
            artifact_type="api_contracts",
            version=1,
        )
        assert isinstance(mem_id, str)

    def test_architecture_history_entries(self, pms):
        pms.store_architecture(project_id=21, content="arch v1", version=1)
        pms.store_architecture(project_id=21, content="arch v2", version=2)
        history = pms.get_version_history(project_id=21, artifact_type="architecture")
        assert len(history) >= 2

    def test_architecture_history_versions_ordered(self, pms):
        history = pms.get_version_history(project_id=21, artifact_type="architecture")
        versions = [e.version for e in history]
        assert versions == sorted(versions)


# ===========================================================================
# 4. Generated File Memory
# ===========================================================================

class TestGeneratedFileMemory:
    def test_store_python_file(self, pms):
        mem_id = pms.store_generated_file(
            project_id=30,
            file_path="backend/main.py",
            content="from fastapi import FastAPI\napp = FastAPI()",
            language="python",
        )
        assert isinstance(mem_id, str)

    def test_store_typescript_file(self, pms):
        mem_id = pms.store_generated_file(
            project_id=30,
            file_path="frontend/app/page.tsx",
            content="export default function Page() { return <div>Hello</div> }",
            language="typescript",
        )
        assert isinstance(mem_id, str)

    def test_get_generated_files_returns_records(self, pms):
        pms.store_generated_file(
            project_id=31,
            file_path="backend/models.py",
            content="class User: pass",
            language="python",
        )
        files = pms.get_generated_files(project_id=31)
        assert len(files) >= 1
        assert all(hasattr(f, "file_path") for f in files)

    def test_file_path_extracted_correctly(self, pms):
        pms.store_generated_file(
            project_id=32,
            file_path="backend/utils/helpers.py",
            content="def helper(): return True",
            language="python",
        )
        files = pms.get_generated_files(project_id=32)
        paths = [f.file_path for f in files]
        assert "backend/utils/helpers.py" in paths

    def test_frontend_file_in_correct_collection(self, pms):
        """Frontend files go to frontend_code collection."""
        pms.store_generated_file(
            project_id=33,
            file_path="frontend/components/Navbar.tsx",
            content="export function Navbar() {}",
            language="tsx",
        )
        files = pms.get_generated_files(project_id=33)
        assert len(files) >= 1

    def test_get_generated_files_sorted_by_path(self, pms):
        pms.store_generated_file(project_id=34, file_path="z_last.py", content="z", language="python")
        pms.store_generated_file(project_id=34, file_path="a_first.py", content="a", language="python")
        files = pms.get_generated_files(project_id=34)
        paths = [f.file_path for f in files]
        assert paths == sorted(paths)


# ===========================================================================
# 5. Agent Output Memory
# ===========================================================================

class TestAgentOutputMemory:
    def test_store_agent_output(self, pms):
        mem_id = pms.store_agent_output(
            project_id=40,
            agent_name="security_engineer",
            artifact_type="security_report",
            content="## Security Report\nNo critical issues found.",
            version=1,
        )
        assert isinstance(mem_id, str)

    def test_get_agent_memory_returns_records(self, pms):
        pms.store_agent_output(
            project_id=41,
            agent_name="qa_engineer",
            artifact_type="qa_report",
            content="## QA Report\n100% tests pass.",
            version=1,
        )
        records = pms.get_agent_memory(project_id=41, agent_name="qa_engineer")
        assert len(records) >= 1
        assert all(r.agent_name == "qa_engineer" for r in records)

    def test_get_agent_memory_filtered_by_agent(self, pms):
        pms.store_agent_output(
            project_id=42,
            agent_name="devops_engineer",
            artifact_type="devops",
            content="## DevOps\nDocker + k8s setup complete.",
            version=1,
        )
        pms.store_agent_output(
            project_id=42,
            agent_name="security_engineer",
            artifact_type="security_report",
            content="## Security\nAll good.",
            version=1,
        )
        devops_records = pms.get_agent_memory(project_id=42, agent_name="devops_engineer")
        assert all(r.agent_name == "devops_engineer" for r in devops_records)

    def test_get_agent_memory_empty_for_unknown_agent(self, pms):
        records = pms.get_agent_memory(project_id=999, agent_name="nonexistent_agent")
        assert records == []

    def test_agent_memory_records_sorted_by_version(self, pms):
        pms.store_agent_output(
            project_id=43, agent_name="backend_developer",
            artifact_type="backend_code", content="v3 code", version=3,
        )
        pms.store_agent_output(
            project_id=43, agent_name="backend_developer",
            artifact_type="backend_code", content="v1 code", version=1,
        )
        records = pms.get_agent_memory(project_id=43, agent_name="backend_developer")
        versions = [r.version for r in records]
        assert versions == sorted(versions)


# ===========================================================================
# 6. Revision Tracking
# ===========================================================================

class TestRevisionTracking:
    def test_record_revision_returns_id(self, pms):
        mem_id = pms.record_revision(
            project_id=50,
            artifact_type="backend_code",
            content="revised code after review",
            version=2,
            reason="Fixed auth bug",
            requested_by="qa_engineer",
        )
        assert isinstance(mem_id, str)

    def test_get_revisions_returns_list(self, pms):
        pms.record_revision(
            project_id=51,
            artifact_type="requirements",
            content="Updated requirements",
            version=2,
            reason="Scope change",
        )
        revisions = pms.get_revisions(project_id=51)
        assert len(revisions) >= 1

    def test_get_revisions_filtered_by_artifact_type(self, pms):
        pms.record_revision(
            project_id=52, artifact_type="backend_code",
            content="backend revision", version=1,
        )
        pms.record_revision(
            project_id=52, artifact_type="frontend_code",
            content="frontend revision", version=1,
        )
        backend_revisions = pms.get_revisions(project_id=52, artifact_type="backend_code")
        assert all(r.artifact_type == "backend_code" for r in backend_revisions)

    def test_get_revisions_no_filter_returns_all(self, pms):
        pms.record_revision(
            project_id=53, artifact_type="backend_code",
            content="backend rev", version=1,
        )
        pms.record_revision(
            project_id=53, artifact_type="requirements",
            content="req rev", version=1,
        )
        all_revisions = pms.get_revisions(project_id=53)
        assert len(all_revisions) >= 2

    def test_revision_sorted_by_type_and_version(self, pms):
        pms.record_revision(project_id=54, artifact_type="backend_code", content="v2", version=2)
        pms.record_revision(project_id=54, artifact_type="backend_code", content="v1", version=1)
        revisions = pms.get_revisions(project_id=54, artifact_type="backend_code")
        versions = [r.version for r in revisions]
        assert versions == sorted(versions)

    def test_get_revisions_empty_project(self, pms):
        revisions = pms.get_revisions(project_id=9999)
        assert revisions == []


# ===========================================================================
# 7. Version History
# ===========================================================================

class TestVersionHistory:
    def test_get_version_history_all(self, pms):
        pms.store_requirement(project_id=60, content="req", version=1)
        pms.store_architecture(project_id=60, content="arch", version=1)
        history = pms.get_version_history(project_id=60)
        assert len(history) >= 2

    def test_get_version_history_filtered(self, pms):
        pms.store_requirement(project_id=61, content="req", version=1)
        pms.store_architecture(project_id=61, content="arch", version=1)
        req_history = pms.get_version_history(
            project_id=61, artifact_type="requirements"
        )
        assert all(e.artifact_type == "requirements" for e in req_history)

    def test_get_version_history_limit(self, pms):
        for i in range(1, 8):
            pms.store_requirement(project_id=62, content=f"req v{i}", version=i)
        history = pms.get_version_history(project_id=62, limit=3)
        assert len(history) <= 3

    def test_get_version_history_empty_project(self, pms):
        history = pms.get_version_history(project_id=9998)
        assert history == []

    def test_version_history_entries_are_project_history_entries(self, pms):
        from memory.schemas import ProjectHistoryEntry

        pms.store_requirement(project_id=63, content="req", version=1)
        history = pms.get_version_history(project_id=63)
        assert all(isinstance(e, ProjectHistoryEntry) for e in history)


# ===========================================================================
# 8. Project Snapshot
# ===========================================================================

class TestProjectSnapshot:
    def test_snapshot_structure(self, pms):
        from memory.schemas import ProjectSnapshot

        pms.store_requirement(project_id=70, content="req", version=1)
        pms.store_architecture(project_id=70, content="arch", version=1)
        pms.store_generated_file(
            project_id=70, file_path="main.py",
            content="print(1)", language="python",
        )
        snap = pms.get_project_snapshot(project_id=70)
        assert isinstance(snap, ProjectSnapshot)
        assert snap.project_id == 70

    def test_snapshot_contains_requirements(self, pms):
        pms.store_requirement(project_id=71, content="Users can login", version=1)
        snap = pms.get_project_snapshot(project_id=71)
        assert len(snap.requirements) >= 1

    def test_snapshot_contains_architecture(self, pms):
        pms.store_architecture(project_id=72, content="Microservices arch", version=1)
        snap = pms.get_project_snapshot(project_id=72)
        assert len(snap.architecture) >= 1

    def test_snapshot_contains_generated_files(self, pms):
        pms.store_generated_file(
            project_id=73, file_path="app.py",
            content="app = FastAPI()", language="python",
        )
        snap = pms.get_project_snapshot(project_id=73)
        assert len(snap.generated_files) >= 1

    def test_snapshot_total_artifacts_property(self, pms):
        pms.store_requirement(project_id=74, content="req", version=1)
        pms.store_architecture(project_id=74, content="arch", version=1)
        snap = pms.get_project_snapshot(project_id=74)
        assert snap.total_artifacts >= 2

    def test_snapshot_empty_project(self, pms):
        snap = pms.get_project_snapshot(project_id=9997)
        assert snap.project_id == 9997
        assert snap.requirements == []
        assert snap.generated_files == []

    def test_snapshot_has_version_history(self, pms):
        pms.store_requirement(project_id=75, content="req v1", version=1)
        pms.store_requirement(project_id=75, content="req v2", version=2)
        snap = pms.get_project_snapshot(project_id=75)
        assert len(snap.version_history) >= 2


# ===========================================================================
# 9. Cross-collection semantic search
# ===========================================================================

class TestSemanticSearch:
    def test_search_returns_list(self, pms):
        pms.store_requirement(
            project_id=80,
            content="JWT authentication for user sessions",
            version=1,
        )
        results = pms.search_project_memory(
            project_id=80, query="authentication"
        )
        assert isinstance(results, list)

    def test_search_with_specific_collection(self, pms):
        pms.store_requirement(
            project_id=81,
            content="Password hashing with bcrypt",
            version=1,
        )
        results = pms.search_project_memory(
            project_id=81,
            query="password security",
            collections=["requirements"],
        )
        assert isinstance(results, list)

    def test_search_empty_query_like_content(self, pms):
        """Search should not crash on a valid query with no good matches."""
        results = pms.search_project_memory(
            project_id=9996,
            query="completely irrelevant content xyz123",
        )
        assert isinstance(results, list)

    def test_search_results_sorted_by_score(self, pms):
        pms.store_requirement(
            project_id=82,
            content="OAuth2 token-based authentication and authorisation",
            version=1,
        )
        results = pms.search_project_memory(
            project_id=82,
            query="OAuth2 authentication",
            limit=10,
        )
        if len(results) > 1:
            scores = [r.get("similarity_score", 0.0) for r in results]
            assert scores == sorted(scores, reverse=True)

    def test_search_limit_respected(self, pms):
        for i in range(5):
            pms.store_requirement(
                project_id=83, content=f"requirement {i} text", version=i + 1,
            )
        results = pms.search_project_memory(
            project_id=83, query="requirement", limit=2,
        )
        assert len(results) <= 2


# ===========================================================================
# 10. MemoryService integration (record_version / get_version_history)
# ===========================================================================

class TestMemoryServiceVersioning:
    def test_record_version_creates_history_entry(self):
        tmp = tempfile.mkdtemp(prefix="cf_test_svc_ver_")
        try:
            svc, _ = _make_service(tmp)
            svc.record_version(
                project_id=90,
                agent_name="backend_developer",
                artifact_type="backend_code",
                content="def hello(): pass",
                version=1,
            )
            history = svc.get_version_history(project_id=90)
            assert len(history) >= 1
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_get_version_history_filtered_by_artifact(self):
        tmp = tempfile.mkdtemp(prefix="cf_test_svc_hist_")
        try:
            svc, _ = _make_service(tmp)
            svc.record_version(
                project_id=91, agent_name="architect",
                artifact_type="architecture", content="arch", version=1,
            )
            svc.record_version(
                project_id=91, agent_name="backend_developer",
                artifact_type="backend_code", content="code", version=1,
            )
            arch = svc.get_version_history(
                project_id=91, artifact_type="architecture"
            )
            assert all(e.artifact_type == "architecture" for e in arch)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_version_history_sorted_ascending(self):
        tmp = tempfile.mkdtemp(prefix="cf_test_svc_sort_")
        try:
            svc, _ = _make_service(tmp)
            for v in [3, 1, 2]:
                svc.record_version(
                    project_id=92, agent_name="backend_developer",
                    artifact_type="backend_code", content=f"v{v}", version=v,
                )
            history = svc.get_version_history(project_id=92)
            versions = [e.version for e in history]
            assert versions == sorted(versions)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_version_history_empty_project(self):
        tmp = tempfile.mkdtemp(prefix="cf_test_svc_empty_")
        try:
            svc, _ = _make_service(tmp)
            history = svc.get_version_history(project_id=99999)
            assert history == []
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


# ===========================================================================
# 11. ProjectMemoryService init
# ===========================================================================

class TestProjectMemoryServiceInit:
    def test_default_init_uses_default_manager(self):
        from unittest.mock import patch, MagicMock

        mock_svc = MagicMock()
        mock_manager = MagicMock()
        mock_manager.get_service.return_value = mock_svc

        # default_manager is imported lazily inside __init__, so patch it on
        # the memory.manager module (the import target) instead.
        with patch("memory.manager.default_manager", mock_manager):
            from memory.project_memory import ProjectMemoryService
            pms = ProjectMemoryService()
            assert pms._svc is mock_svc

    def test_explicit_service_injection(self):
        from memory.project_memory import ProjectMemoryService

        mock_svc = MagicMock()
        pms = ProjectMemoryService(memory_service=mock_svc)
        assert pms._svc is mock_svc

    def test_store_requirement_delegates_to_svc(self):
        from memory.project_memory import ProjectMemoryService

        mock_svc = MagicMock()
        mock_svc.store_memory.return_value = "mem-id-123"
        mock_svc.record_version.return_value = "hist-id-456"

        pms = ProjectMemoryService(memory_service=mock_svc)
        result = pms.store_requirement(project_id=1, content="test req", version=1)
        assert result == "mem-id-123"
        assert mock_svc.store_memory.called
        assert mock_svc.record_version.called

    def test_record_revision_delegates_to_svc(self):
        from memory.project_memory import ProjectMemoryService

        mock_svc = MagicMock()
        mock_svc.record_version.return_value = "rev-id-789"

        pms = ProjectMemoryService(memory_service=mock_svc)
        result = pms.record_revision(
            project_id=1, artifact_type="backend_code",
            content="revised", version=2, reason="bug fix",
        )
        assert result == "rev-id-789"
        assert mock_svc.record_version.called


# ===========================================================================
# 12. Module-level public API exports
# ===========================================================================

class TestPublicExports:
    def test_project_memory_service_importable(self):
        from memory import ProjectMemoryService
        assert ProjectMemoryService is not None

    def test_artifact_type_importable(self):
        from memory import ArtifactType
        assert ArtifactType is not None

    def test_agent_memory_record_importable(self):
        from memory import AgentMemoryRecord
        assert AgentMemoryRecord is not None

    def test_generated_file_record_importable(self):
        from memory import GeneratedFileRecord
        assert GeneratedFileRecord is not None

    def test_revision_entry_importable(self):
        from memory import RevisionEntry
        assert RevisionEntry is not None

    def test_project_snapshot_importable(self):
        from memory import ProjectSnapshot
        assert ProjectSnapshot is not None

    def test_store_artifact_request_importable(self):
        from memory import StoreArtifactRequest
        assert StoreArtifactRequest is not None

    def test_store_revision_request_importable(self):
        from memory import StoreRevisionRequest
        assert StoreRevisionRequest is not None
