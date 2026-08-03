"""
Regression Tests — Phase 5.6
"""
import pytest
from app.main import app


def test_ai_mode_routes_registered():
    all_paths = []
    for r in app.routes:
        if hasattr(r, "path"):
            all_paths.append(r.path)
        elif hasattr(r, "original_router"):
            prefix = getattr(r.include_context, "prefix", "") if hasattr(r, "include_context") else ""
            for sub_r in r.original_router.routes:
                if hasattr(sub_r, "path"):
                    all_paths.append(prefix + sub_r.path)

    assert len(all_paths) > 0
    assert any("/ai-mode" in p for p in all_paths)
    assert any("/context" in p for p in all_paths)
    assert any("collaboration" in p for p in all_paths)
    assert any("rag" in p for p in all_paths)
    assert any("approval" in p for p in all_paths)
