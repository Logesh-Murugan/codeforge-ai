"""
ContextScoringService — Phase 5.5

Context Scoring System. Evaluates 6 quality scores:
1. Relevancy Score
2. Confidence Score
3. Priority Score
4. Freshness Score
5. Source Score
6. Overall Quality Score
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from context_engine.schemas.scoring import ContextQualityScoreResponse
from context_engine.utils.scoring_math import calculate_freshness_score, calculate_overall_quality

logger = logging.getLogger(__name__)


class ContextScoringService:
    """
    Context Scoring System.
    """

    async def evaluate_context_quality(
        self, project_id: int, context_bundle: Dict[str, Any], context_type: str = "Bundle"
    ) -> ContextQualityScoreResponse:
        """
        Evaluate 6 quality scores for a context bundle.
        """
        has_content = bool(context_bundle)

        relevancy = 1.0 if has_content else 0.2
        confidence = 0.95 if has_content else 0.5
        priority = 0.9 if context_type in ("Security", "Architecture", "API") else 0.8
        freshness = calculate_freshness_score(datetime.now(timezone.utc))
        source_score = 0.95

        overall = calculate_overall_quality(
            relevancy=relevancy,
            confidence=confidence,
            priority=priority,
            freshness=freshness,
            source=source_score,
        )

        return ContextQualityScoreResponse(
            project_id=project_id,
            context_type=context_type,
            relevancy_score=relevancy,
            confidence_score=confidence,
            priority_score=priority,
            freshness_score=freshness,
            source_score=source_score,
            overall_quality_score=overall,
        )
