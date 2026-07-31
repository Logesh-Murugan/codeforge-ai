"""
Cross Validation Tests — Phase 5.4

Tests for CrossValidationService.
"""
import pytest
from collaboration.schemas.validation import CrossValidationRequest
from collaboration.services.cross_validation_service import CrossValidationService


@pytest.mark.asyncio
async def test_cross_validation_security_engineer():
    service = CrossValidationService()
    req = CrossValidationRequest(
        project_id=42,
        validator_agent="security_engineer",
        target_agent="backend_developer",
        target_output={"code": "from fastapi import FastAPI; app = FastAPI()", "auth": "JWT"},
    )
    res = await service.validate_output(req)
    assert res.is_valid is True
    assert res.agreement_score >= 0.8
    assert len(res.rule_results) >= 2


@pytest.mark.asyncio
async def test_cross_validation_qa_engineer():
    service = CrossValidationService()
    req = CrossValidationRequest(
        project_id=42,
        validator_agent="qa_engineer",
        target_agent="api_designer",
        target_output={"endpoints": [{"path": "/api/users", "method": "GET"}]},
    )
    res = await service.validate_output(req)
    assert res.is_valid is True
    assert res.agreement_score >= 0.8
