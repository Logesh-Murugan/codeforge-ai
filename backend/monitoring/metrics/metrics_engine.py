"""
MetricsEngine — Phase 5.7

Metrics calculation engine.
"""
from __future__ import annotations

import logging
from typing import Dict, List

from monitoring.schemas.metrics import MonitoringMetricsResponse

logger = logging.getLogger(__name__)


class MetricsEngine:
    """
    Metrics Engine.
    """

    def calculate_success_rate(self, total_runs: int, failures: int) -> float:
        """Calculate success rate percentage."""
        if total_runs == 0:
            return 100.0
        rate = ((total_runs - failures) / total_runs) * 100.0
        return round(max(0.0, min(100.0, rate)), 1)

    def calculate_average_runtime(self, runtimes_ms: List[float]) -> float:
        """Calculate average agent runtime."""
        if not runtimes_ms:
            return 0.0
        return round(sum(runtimes_ms) / len(runtimes_ms), 1)
