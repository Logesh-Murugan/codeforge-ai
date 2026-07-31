"""
Context Scoring Tests — Phase 5.5
"""
import pytest
from datetime import datetime, timezone
from context_engine.services.context_scoring_service import ContextScoringService
from context_engine.utils.scoring_math import calculate_freshness_score, calculate_overall_quality


def test_calculate_freshness_score():
    now = datetime.now(timezone.utc)
    fresh_score = calculate_freshness_score(now)
    assert fresh_score == 1.0


def test_calculate_overall_quality():
    quality = calculate_overall_quality(1.0, 0.95, 0.9, 1.0, 0.95)
    assert quality >= 0.9


@pytest.mark.asyncio
async def test_evaluate_context_quality():
    scoring = ContextScoringService()
    bundle = {"Architecture": {"arch": "clean"}}
    res = await scoring.evaluate_context_quality(42, bundle, "Architecture")

    assert res.project_id == 42
    assert res.overall_quality_score > 0.5
    assert res.relevancy_score == 1.0
