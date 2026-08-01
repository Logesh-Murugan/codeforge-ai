"""
Regression Tests — Phase 5.8
"""
import pytest
from app.main import app


def test_validation_routes_registered():
    all_paths = [getattr(r, "path", str(r)) for r in app.routes]
    assert len(all_paths) > 0
    assert any("/validation" in p for p in all_paths)
    assert any("/monitoring" in p for p in all_paths)
    assert any("/ai-mode" in p for p in all_paths)
    assert any("/context" in p for p in all_paths)
