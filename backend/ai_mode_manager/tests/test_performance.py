"""
Performance Tests — Phase 5.6
"""
import time
import pytest
from ai_mode_manager.registry.provider_registry import provider_registry


def test_registry_lookup_performance():
    start = time.time()
    for _ in range(1000):
        _ = provider_registry.get_provider("groq")
    elapsed = time.time() - start

    assert elapsed < 0.05  # O(1) 1000 lookups must execute under 50ms
