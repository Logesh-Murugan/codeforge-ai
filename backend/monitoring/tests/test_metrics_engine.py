"""
MetricsEngine Tests — Phase 5.7
"""
import pytest
from monitoring.metrics.metrics_engine import MetricsEngine


def test_metrics_engine_calculations():
    engine = MetricsEngine()
    
    sr = engine.calculate_success_rate(10, 2)
    assert sr == 80.0

    avg_rt = engine.calculate_average_runtime([100.0, 200.0, 300.0])
    assert avg_rt == 200.0
