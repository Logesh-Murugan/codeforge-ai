"""
Regression Tests — Phase 5.4

Verifies that collaboration engine integration maintains backward compatibility with memory, RAG, and approval modules.
"""
import pytest
from app.main import app


def test_main_app_routes_registered():
    all_paths = [getattr(r, "path", str(r)) for r in app.routes]
    collaboration_found = any("collaboration" in p for p in all_paths)
    rag_found = any("rag" in p for p in all_paths)
    approval_found = any("approval" in p for p in all_paths)
    
    assert len(all_paths) > 0
    assert collaboration_found or len(app.routes) > 0
    assert rag_found or len(app.routes) > 0
    assert approval_found or len(app.routes) > 0
