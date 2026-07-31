"""
Scoring Math Utility — Phase 5.5

Calculates 6-tier quality score metrics: Relevancy, Confidence, Priority, Freshness, Source, Overall.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Dict, List


def calculate_freshness_score(created_at: datetime, decay_rate: float = 0.1) -> float:
    """
    Time decay function: score = 1.0 / (1 + age_in_hours * decay_rate).
    """
    now = datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    age_hours = max(0.0, (now - created_at).total_seconds() / 3600.0)
    score = 1.0 / (1.0 + age_hours * decay_rate)
    return round(max(0.1, min(1.0, score)), 2)


def calculate_overall_quality(
    relevancy: float,
    confidence: float,
    priority: float,
    freshness: float,
    source: float,
) -> float:
    """
    Weighted composite quality index:
        Quality = 0.25*Relevancy + 0.20*Confidence + 0.20*Priority + 0.15*Freshness + 0.20*Source
    """
    quality = (
        (0.25 * relevancy)
        + (0.20 * confidence)
        + (0.20 * priority)
        + (0.15 * freshness)
        + (0.20 * source)
    )
    return round(max(0.0, min(1.0, quality)), 2)
