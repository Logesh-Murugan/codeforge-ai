"""
Unit Tests — Phase 5.4

Unit tests for collaboration utils, schemas, and scoring formulas.
"""
import pytest
from collaboration.schemas.communication import CommunicationPattern
from collaboration.utils.patterns import resolve_communication_topology
from collaboration.utils.scoring import calculate_collaboration_metrics


def test_resolve_communication_topology_sequential():
    routes = resolve_communication_topology(
        CommunicationPattern.SEQUENTIAL, "backend_developer", ["security_engineer", "qa_engineer"]
    )
    assert len(routes) == 2
    assert routes[0]["mode"] == "sync"


def test_resolve_communication_topology_parallel():
    routes = resolve_communication_topology(
        CommunicationPattern.PARALLEL, "solution_architect", ["database_engineer", "api_designer"]
    )
    assert len(routes) == 2
    assert routes[0]["mode"] == "async"


def test_calculate_collaboration_metrics():
    metrics = calculate_collaboration_metrics(
        total_messages=10,
        total_validations=5,
        passed_validations=5,
        total_feedback_entries=1,
        resolved_feedback_entries=1,
        agreement_scores=[0.9, 0.95, 1.0],
    )
    assert metrics["overall_score"] > 0.5
    assert metrics["consensus_rating"] >= 0.9
    assert metrics["friction_score"] == 0.0
