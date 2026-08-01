"""
Severity & Grade Tests — Phase 5.8
"""
import pytest
from validation_pipeline.severity import IssueSeverity, PipelineStatus, QualityGrade
from validation_pipeline.validator_result import PipelineResult


def test_severity_enums():
    assert IssueSeverity.CRITICAL == "CRITICAL"
    assert PipelineStatus.PASSED == "PASSED"
    assert QualityGrade.A_PLUS == "A+"


def test_grade_calculation():
    assert PipelineResult.calculate_grade(97.0) == QualityGrade.A_PLUS
    assert PipelineResult.calculate_grade(92.0) == QualityGrade.A
    assert PipelineResult.calculate_grade(85.0) == QualityGrade.B
    assert PipelineResult.calculate_grade(75.0) == QualityGrade.C
    assert PipelineResult.calculate_grade(65.0) == QualityGrade.D
    assert PipelineResult.calculate_grade(50.0) == QualityGrade.F
