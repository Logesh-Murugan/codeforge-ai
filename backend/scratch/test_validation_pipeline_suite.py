"""
Verification Suite — Phase 5.8 Validation Pipeline System
"""
import asyncio
import sys

from validation_pipeline.severity import IssueSeverity, PipelineStatus, QualityGrade
from validation_pipeline.validator_result import PipelineResult, ValidationIssue
from validation_pipeline.validator_registry import validator_registry
from validation_pipeline.pipeline import pipeline
from validation_pipeline.report_generator import report_generator
from validation_pipeline.validators import (
    StructureValidator,
    SyntaxValidator,
    DependencyValidator,
    ArchitectureValidator,
    DatabaseValidator,
    ApiValidator,
    SecurityValidator,
    DocumentationValidator,
    DockerValidator,
    TestingValidator,
    PerformanceValidator,
    CodeQualityValidator,
)


async def run_all_tests():
    print("--- 1. Testing Severity System & Quality Grades ---")
    assert IssueSeverity.CRITICAL == "CRITICAL"
    assert PipelineStatus.PASSED == "PASSED"
    assert QualityGrade.A_PLUS == "A+"
    assert PipelineResult.calculate_grade(98.0) == QualityGrade.A_PLUS
    assert PipelineResult.calculate_grade(75.0) == QualityGrade.C
    print("Severity & grade tests PASSED [OK]")

    print("\n--- 2. Testing 12 Concrete Stage Validators ---")
    validators = [
        StructureValidator(),
        SyntaxValidator(),
        DependencyValidator(),
        ArchitectureValidator(),
        DatabaseValidator(),
        ApiValidator(),
        SecurityValidator(),
        DocumentationValidator(),
        DockerValidator(),
        TestingValidator(),
        PerformanceValidator(),
        CodeQualityValidator(),
    ]
    assert len(validators) == 12

    for val in validators:
        res = await val.validate(".", context={})
        assert res.stage_name == val.stage_name
        assert res.score >= 0.0
    print("12 Stage Validators tests PASSED [OK]")

    print("\n--- 3. Testing 12-Stage Pipeline Execution ---")
    pipeline_res = await pipeline.execute_pipeline(project_id=1, project_path=".")
    assert pipeline_res.project_id == 1
    assert len(pipeline_res.stage_results) == 12
    assert pipeline_res.overall_score >= 0.0
    assert isinstance(pipeline_res.quality_grade, QualityGrade)
    print("12-Stage Pipeline execution tests PASSED [OK]")

    print("\n--- 4. Testing Automated Report Generator (7 Reports) ---")
    reports = report_generator.generate_all_reports(pipeline_res)
    assert "validation_summary.md" in reports
    assert "validation_details.md" in reports
    assert "security_report.md" in reports
    assert "architecture_report.md" in reports
    assert "performance_report.md" in reports
    assert "quality_score.md" in reports
    assert "validation.json" in reports
    print("Report Generator tests PASSED [OK]")

    print("\n==========================================")
    print("ALL PHASE 5.8 VALIDATION PIPELINE TESTS PASSED SUCCESSFULLY! [OK]")
    print("==========================================")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
