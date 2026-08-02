"""
Verification Suite — Phase 5.9 Project Timeline System
"""
import asyncio
import sys

from timeline.config import timeline_settings
from timeline.schemas.timeline_schema import TimelineEventDTO, MilestoneDTO, ProgressDTO, TimelineAnalyticsDTO
from timeline.services.timeline_service import timeline_service
from timeline.services.milestone_service import milestone_service
from timeline.services.analytics_service import analytics_service
from timeline.services.progress_service import progress_service
from timeline.reports.report_generator import report_generator


async def run_all_tests():
    print("--- 1. Testing Timeline Config ---")
    assert timeline_settings.MAX_TIMELINE_HISTORY_EVENTS == 5000
    assert timeline_settings.AUTO_DETECT_MILESTONES is True
    print("Config tests PASSED [OK]")

    print("\n--- 2. Testing TimelineService (Record & Retrieve) ---")
    evt = TimelineEventDTO(
        event_id="EVT-VERIFY",
        project_id=1,
        agent_name="backend_developer",
        stage_name="Backend Generation",
        status="COMPLETED",
        duration_ms=250.0,
    )
    recorded = await timeline_service.record_event(evt)
    assert recorded.event_id == "EVT-VERIFY"

    events = await timeline_service.get_project_timeline(project_id=1)
    assert len(events) >= 1
    assert any(e.event_id == "EVT-VERIFY" for e in events)
    print("TimelineService tests PASSED [OK]")

    print("\n--- 3. Testing MilestoneService (9 Milestones) ---")
    milestones = await milestone_service.get_project_milestones(project_id=1)
    assert len(milestones) == 9
    assert any(m.milestone_name == "Requirements Complete" for m in milestones)
    assert any(m.milestone_name == "Deployment Ready & Exported" for m in milestones)
    print("MilestoneService tests PASSED [OK]")

    print("\n--- 4. Testing Analytics & Progress Services ---")
    analytics = await analytics_service.get_project_analytics(project_id=1)
    assert analytics.project_id == 1
    assert analytics.total_events > 0

    progress = await progress_service.get_project_progress(project_id=1)
    assert progress.project_id == 1
    assert progress.overall_progress_pct == 100.0
    print("Analytics & Progress tests PASSED [OK]")

    print("\n--- 5. Testing Multi-Format Report Generator (MD, JSON, HTML) ---")
    reports = report_generator.generate_all_reports(events)
    assert "timeline_report.md" in reports
    assert "performance_report.md" in reports
    assert "execution_report.md" in reports
    assert "milestone_report.md" in reports
    assert "analytics_report.md" in reports
    assert "timeline.json" in reports
    assert "timeline_report.html" in reports
    print("Report Generator tests PASSED [OK]")

    print("\n==========================================")
    print("ALL PHASE 5.9 TIMELINE TESTS PASSED SUCCESSFULLY! [OK]")
    print("==========================================")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
