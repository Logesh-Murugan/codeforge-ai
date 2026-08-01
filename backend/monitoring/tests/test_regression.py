"""
Regression Tests — Phase 5.7
"""
import pytest
from app.main import app


def test_monitoring_routes_registered():
    all_paths = [getattr(r, "path", str(r)) for r in app.routes]
    assert len(all_paths) > 0
    assert any("/monitoring" in p for p in all_paths)
    assert any("/ws/monitoring" in p for p in all_paths)
    assert any("/ai-mode" in p for p in all_paths)
    assert any("/context" in p for p in all_paths)
