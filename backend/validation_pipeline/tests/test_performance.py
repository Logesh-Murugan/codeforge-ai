"""
Performance Tests — Phase 5.8
"""
import time
import pytest
from validation_pipeline.pipeline import pipeline


@pytest.mark.asyncio
async def test_pipeline_performance():
    t0 = time.perf_counter()
    res = await pipeline.execute_pipeline(project_id=1, project_path=".")
    duration_ms = (time.perf_counter() - t0) * 1000.0

    assert res is not None
    assert duration_ms < 500.0  # 12-stage validation must execute in <500ms
