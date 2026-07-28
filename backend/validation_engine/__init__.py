"""
CodeForge AI — Validation Engine (Phase 4.2)
=============================================

Automatically validates generated projects across six categories:
- Source Code (folder structure, imports, deps, configs)
- FastAPI (routers, endpoints, models, middleware)
- Database (SQLAlchemy models, migrations, async)
- Authentication (JWT, ownership, RBAC)
- Documentation (README, deployment guide, API docs)
- Docker (Dockerfile, compose, env config)

Produces a ValidationReport with PASS/FAIL, errors, warnings,
recommendations, and a production readiness score (0–100).
"""
from validation_engine.schemas import (
    ValidationSeverity,
    ValidationStatus,
    ValidationIssue,
    CategoryResult,
    ValidationReport,
    ValidationRequest,
)
from validation_engine.engine import ValidationEngine

__all__ = [
    "ValidationSeverity",
    "ValidationStatus",
    "ValidationIssue",
    "CategoryResult",
    "ValidationReport",
    "ValidationRequest",
    "ValidationEngine",
]
