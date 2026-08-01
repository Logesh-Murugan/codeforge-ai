"""
Configuration Tests — Phase 5.6
"""
import pytest
from ai_mode_manager.services.mode_manager import mode_manager
from ai_mode_manager.schemas.request_response import UpdateConfigRequest
from ai_mode_manager.schemas.mode_state import WorkingMode


@pytest.mark.asyncio
async def test_update_configuration():
    res = await mode_manager.update_configuration(
        UpdateConfigRequest(model="llama-3.3-70b")
    )
    assert res.active_model == "llama-3.3-70b"


def test_validate_configuration():
    val = mode_manager.validate_configuration()
    assert "is_valid" in val
