"""
Regression Tests — Phase 5.9
"""
import pytest
from app.main import app


def test_timeline_routes_registered():
    all_paths = [getattr(r, "path", str(r)) for r in app.routes]
    assert len(all_paths) > 0
    assert any("/timeline" in p for p in all_paths)
    assert any("/validation" in p for p in all_paths)
    assert any("/monitoring" in p for p in all_paths)
    assert any("/ai-mode" in p for p in all_paths)
