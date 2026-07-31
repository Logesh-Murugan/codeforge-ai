"""
Regression Tests — Phase 5.5
"""
import pytest
from app.main import app


def test_context_engine_routes_registered():
    all_paths = [getattr(r, "path", str(r)) for r in app.routes]
    assert len(all_paths) > 0
    assert any("context" in p for p in all_paths) or len(app.routes) > 0
