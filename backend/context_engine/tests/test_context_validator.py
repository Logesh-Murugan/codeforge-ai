"""
Context Validation Tests — Phase 5.5
"""
import pytest
from context_engine.validators.context_validator import ContextValidator


@pytest.mark.asyncio
async def test_validate_bundle_detects_missing_contexts():
    validator = ContextValidator()
    bundle = {"Project": {"id": 42}}
    required = ["Project", "Architecture", "Database"]

    res = await validator.validate_bundle(42, "backend_developer", bundle, required)
    assert res.is_valid is True  # Warning level issues, gracefully valid
    assert res.total_issues == 2  # Architecture & Database missing


@pytest.mark.asyncio
async def test_validate_bundle_detects_empty_contexts():
    validator = ContextValidator()
    bundle = {"Project": {"id": 42}, "EmptyType": {}}
    res = await validator.validate_bundle(42, "backend_developer", bundle)

    assert res.total_issues >= 1
