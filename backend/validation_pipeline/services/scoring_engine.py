"""
Weighted Scoring Engine — Phase 5.8

Weighted Scoring Categories:
- Architecture: 15%
- Security: 20%
- Backend: 15%
- Frontend: 10%
- API: 10%
- Database: 10%
- Testing: 10%
- Documentation: 5%
- Deployment: 5%
- Performance: 10%
"""
from __future__ import annotations

import logging
from typing import Dict
from validation_pipeline.severity import QualityGrade

logger = logging.getLogger(__name__)


class ScoringEngine:
    """
    Weighted Quality Scoring Engine.
    """

    WEIGHTS = {
        "architecture": 0.15,
        "security": 0.20,
        "backend": 0.15,
        "frontend": 0.10,
        "api": 0.10,
        "database": 0.10,
        "testing": 0.10,
        "documentation": 0.05,
        "deployment": 0.05,
        "performance": 0.10,
    }

    def calculate_weighted_score(self, category_scores: Dict[str, float]) -> float:
        """Calculate weighted score out of 100."""
        total = 0.0
        for category, weight in self.WEIGHTS.items():
            score = category_scores.get(category, 100.0)
            total += score * weight
        return round(total, 1)

    def get_quality_grade_label(self, score: float) -> str:
        """Return human readable Quality Grade Label."""
        if score >= 95.0:
            return "Production Ready (A+)"
        elif score >= 90.0:
            return "Excellent (A)"
        elif score >= 80.0:
            return "Good (B)"
        elif score >= 70.0:
            return "Needs Improvement (C)"
        else:
            return "Failed (F)"


scoring_engine = ScoringEngine()
