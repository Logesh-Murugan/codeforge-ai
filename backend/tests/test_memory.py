"""
Existing memory CRUD smoke tests — updated for new package structure.

These tests preserve the original assertions while importing from the
new canonical paths.  They remain as a regression guard for the full
store → retrieve → delete lifecycle.
"""
import pytest
import shutil
import tempfile

from memory.embeddings.local import LocalEmbeddings
from memory.vectorstores.chroma import ChromaVectorStore
from memory.service import MemoryService


@pytest.fixture(scope="module")
def temp_chroma_dir():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_local_embeddings():
    """Verify LocalEmbeddings yields correct dimensions and normalises output."""
    provider = LocalEmbeddings(dim=1536)
    vec = provider.embed_query("A test query.")
    assert len(vec) == 1536
    norm = sum(v * v for v in vec) ** 0.5
    assert abs(norm - 1.0) < 1e-5


def test_memory_crud_operations(temp_chroma_dir):
    """Full storage, similarity retrieval, thresholding, and deletion lifecycle."""
    store = ChromaVectorStore(persist_path=temp_chroma_dir)
    service = MemoryService(
        embedding_provider=LocalEmbeddings(dim=1536),
        vector_store=store,
    )

    project_id = 999

    doc1 = "The database design must use a normalized PostgreSQL schema."
    doc2 = "The frontend dashboard uses Next.js and React query hooks."

    id1 = service.store_memory(
        project_id=project_id,
        agent_name="database_engineer",
        artifact_type="db_schema",
        collection_name="database_design",
        content=doc1,
        version=1,
    )

    id2 = service.store_memory(
        project_id=project_id,
        agent_name="frontend_developer",
        artifact_type="page_component",
        collection_name="frontend_code",
        content=doc2,
        version=1,
    )

    assert id1 != ""
    assert id2 != ""

    # Raw listing
    db_mem = service.get_project_memory(project_id, "database_design")
    assert len(db_mem) == 1
    assert db_mem[0]["document"] == doc1
    assert db_mem[0]["metadata"]["agent_name"] == "database_engineer"
    assert db_mem[0]["id"] == id1

    # Semantic search — should find the DB doc
    matches = service.retrieve_memory(
        project_id=project_id,
        collection_name="database_design",
        query="PostgreSQL schemas database design",
        limit=2,
        threshold=0.1,
    )
    assert len(matches) == 1
    assert matches[0]["document"] == doc1
    assert matches[0]["similarity_score"] > 0.1

    # High threshold should filter out poor matches
    no_matches = service.retrieve_memory(
        project_id=project_id,
        collection_name="database_design",
        query="Frontend dashboard setup instructions",
        limit=2,
        threshold=0.9,
    )
    assert len(no_matches) == 0

    # Delete + verify
    service.delete_project_memory(project_id)

    db_mem_after = service.get_project_memory(project_id, "database_design")
    fe_mem_after = service.get_project_memory(project_id, "frontend_code")
    assert len(db_mem_after) == 0
    assert len(fe_mem_after) == 0
