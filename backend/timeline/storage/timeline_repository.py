"""
TimelineRepository — Phase 5.9

Repository Pattern for timeline events & milestone persistence.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from timeline.models import MilestoneModel, TimelineEventModel

logger = logging.getLogger(__name__)


class TimelineRepository:
    """
    Timeline Repository.
    """

    def create_event(self, db: Session, event_data: Dict[str, Any]) -> TimelineEventModel:
        """Persist a new timeline event into database."""
        event_record = TimelineEventModel(**event_data)
        db.add(event_record)
        db.commit()
        db.refresh(event_record)
        return event_record

    def get_events_by_project(self, db: Session, project_id: int, limit: int = 100) -> List[TimelineEventModel]:
        """Retrieve timeline events for project_id."""
        return (
            db.query(TimelineEventModel)
            .filter(TimelineEventModel.project_id == project_id)
            .order_by(TimelineEventModel.timestamp.desc())
            .limit(limit)
            .all()
        )

    def create_milestone(self, db: Session, milestone_data: Dict[str, Any]) -> MilestoneModel:
        """Persist milestone achievement into database."""
        milestone = MilestoneModel(**milestone_data)
        db.add(milestone)
        db.commit()
        db.refresh(milestone)
        return milestone

    def get_milestones_by_project(self, db: Session, project_id: int) -> List[MilestoneModel]:
        """Retrieve all milestone records for project_id."""
        return (
            db.query(MilestoneModel)
            .filter(MilestoneModel.project_id == project_id)
            .order_by(MilestoneModel.achieved_at.asc())
            .all()
        )


timeline_repository = TimelineRepository()
