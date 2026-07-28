"""
CodeForge AI — Testing Engine (Phase 4.4)
==========================================

Automatically validates generated projects across 15 checks in a
self-test pipeline.
"""
from testing_engine.schemas import (
    TestStatus,
    TestResult,
    TestingReport,
    TestingRequest,
)
from testing_engine.engine import TestingEngine

__all__ = [
    "TestStatus",
    "TestResult",
    "TestingReport",
    "TestingRequest",
    "TestingEngine",
]
