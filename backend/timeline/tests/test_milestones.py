"""
MilestoneService Tests — Phase 5.9
"""
import pytest
from timeline.services.milestone_service import MilestoneService


@pytest.mark.asyncio
async def test_milestone_detection():
    service = MilestoneService()
    milestones = await service.get_project_milestones(project_id=1)
    assert len(milestones) == 9
    assert any(m.milestone_name == "Requirements Complete" for m in milestones)
    assert any(m.milestone_name == "Deployment Ready & Exported" for m in milestones)
