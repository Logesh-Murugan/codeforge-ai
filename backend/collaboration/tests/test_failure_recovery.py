"""
Failure Recovery Tests — Phase 5.4

Tests graceful error handling and recovery when context or validation inputs are missing.
"""
import pytest
from collaboration.schemas.validation import CrossValidationRequest
from collaboration.services.cross_validation_service import CrossValidationService
from collaboration.services.context_exchange_service import ContextExchangeService


@pytest.mark.asyncio
async def test_empty_output_validation_failure_recovery():
    service = CrossValidationService()
    req = CrossValidationRequest(
        project_id=42,
        validator_agent="security_engineer",
        target_agent="backend_developer",
        target_output={},
    )
    res = await service.validate_output(req)
    assert res.is_valid is False
    assert res.agreement_score < 1.0


@pytest.mark.asyncio
async def test_context_exchange_graceful_fallback():
    service = ContextExchangeService()
    bundle = await service.assemble_context_bundle(99999, "backend_developer")
    assert bundle.project_id == 99999
    assert bundle.target_agent == "backend_developer"
