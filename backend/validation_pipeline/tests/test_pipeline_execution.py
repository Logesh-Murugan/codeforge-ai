"""
Pipeline Execution Tests — Phase 5.8
"""
import pytest
from validation_pipeline.pipeline import pipeline
from validation_pipeline.severity import PipelineStatus, QualityGrade


@pytest.mark.asyncio
async def test_pipeline_execution():
    res = await pipeline.execute_pipeline(project_id=1, project_path=".")
    assert res.project_id == 1
    assert len(res.stage_results) == 12
    assert res.overall_score >= 0.0
    assert isinstance(res.quality_grade, QualityGrade)
