"""
Scoring Utility — Phase 5.4

Algorithms to compute collaboration density, consensus rating, friction score, and overall collaboration score.
"""
from __future__ import annotations

from typing import List


def calculate_collaboration_metrics(
    total_messages: int,
    total_validations: int,
    passed_validations: int,
    total_feedback_entries: int,
    resolved_feedback_entries: int,
    agreement_scores: List[float],
) -> dict:
    """
    Calculate standardized collaboration scores.

    Returns:
        dict with keys: overall_score, consensus_rating, information_density, friction_score
    """
    # Consensus Rating: Average agreement score from validations
    if agreement_scores:
        consensus_rating = sum(agreement_scores) / len(agreement_scores)
    elif total_validations > 0:
        consensus_rating = passed_validations / total_validations
    else:
        consensus_rating = 1.0

    # Information Density: Ratio of messages to minimum baseline
    information_density = min(1.0, max(0.1, total_messages / 20.0)) if total_messages > 0 else 0.5

    # Friction Score: Unresolved feedback or failed validations ratio
    failed_validations = max(0, total_validations - passed_validations)
    unresolved_feedback = max(0, total_feedback_entries - resolved_feedback_entries)
    friction_count = failed_validations + unresolved_feedback
    friction_score = min(1.0, friction_count / 10.0)

    # Overall Score formula
    overall_score = round(
        max(0.0, min(1.0, (consensus_rating * 0.5) + (information_density * 0.3) + ((1.0 - friction_score) * 0.2))),
        2
    )

    return {
        "overall_score": overall_score,
        "consensus_rating": round(consensus_rating, 2),
        "information_density": round(information_density, 2),
        "friction_score": round(friction_score, 2),
    }
