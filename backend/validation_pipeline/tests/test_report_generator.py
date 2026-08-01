"""
Report Generator Tests — Phase 5.8
"""
import pytest
from validation_pipeline.pipeline import pipeline
from validation_pipeline.report_generator import report_generator


@pytest.mark.asyncio
async def test_report_generator():
    res = await pipeline.execute_pipeline(project_id=1, project_path=".")
    reports = report_generator.generate_all_reports(res)
    
    assert "validation_summary.md" in reports
    assert "validation_details.md" in reports
    assert "security_report.md" in reports
    assert "architecture_report.md" in reports
    assert "performance_report.md" in reports
    assert "quality_score.md" in reports
    assert "validation.json" in reports
