"""
12 Validators Tests — Phase 5.8
"""
import pytest
from validation_pipeline.validators import (
    ApiValidator,
    ArchitectureValidator,
    CodeQualityValidator,
    DatabaseValidator,
    DependencyValidator,
    DockerValidator,
    DocumentationValidator,
    PerformanceValidator,
    SecurityValidator,
    StructureValidator,
    SyntaxValidator,
    TestingValidator,
)


@pytest.mark.asyncio
async def test_all_12_validators():
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

    for v in validators:
        res = await v.validate(".", context={})
        assert res.stage_name == v.stage_name
        assert res.score >= 0.0
