"""
Context Aggregation Tests — Phase 5.5
"""
import pytest
from context_engine.aggregators.context_aggregator import ContextAggregator


@pytest.mark.asyncio
async def test_aggregate_all_sources_returns_master_bundle():
    aggregator = ContextAggregator()
    bundle = await aggregator.aggregate_all_sources(42)

    assert isinstance(bundle, dict)
    assert "Project" in bundle
    assert "Memory" in bundle
    assert "RAG" in bundle
    assert "Collaboration" in bundle
