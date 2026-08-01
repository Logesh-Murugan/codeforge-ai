"""
Regression Tests — Phase 5.6
"""
import pytest
from app.main import app


def test_ai_mode_routes_registered():
    all_paths = [getattr(r, "path", str(r)) for r in app.routes]
    assert len(all_paths) > 0
    assert any("/ai-mode" in p for p in all_paths)
    assert any("/context" in p for p in all_paths)
    assert any("collaboration" in p for p in all_paths)
    assert any("rag" in p for p in all_paths)
    assert any("approval" in p for p in all_paths)
