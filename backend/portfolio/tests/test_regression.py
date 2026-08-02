"""
Regression Tests — Phase 5.10
"""
import pytest
from app.main import app


def test_portfolio_routes_registered():
    all_paths = [getattr(r, "path", str(r)) for r in app.routes]
    assert len(all_paths) > 0
    assert any("/portfolio" in p for p in all_paths)
    assert any("/timeline" in p for p in all_paths)
    assert any("/validation" in p for p in all_paths)
