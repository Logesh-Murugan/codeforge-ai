"""
Mode Switching Tests — Phase 5.6
"""
import pytest
from ai_mode_manager.services.mode_manager import mode_manager
from ai_mode_manager.schemas.mode_state import WorkingMode


@pytest.mark.asyncio
async def test_switch_mode_to_local_and_cloud():
    # Switch to LOCAL
    cfg_local = await mode_manager.switch_mode(WorkingMode.LOCAL)
    assert cfg_local.mode == WorkingMode.LOCAL
    assert mode_manager.get_current_mode() == WorkingMode.LOCAL

    # Switch back to CLOUD
    cfg_cloud = await mode_manager.switch_mode(WorkingMode.CLOUD)
    assert cfg_cloud.mode == WorkingMode.CLOUD
    assert mode_manager.get_current_mode() == WorkingMode.CLOUD
