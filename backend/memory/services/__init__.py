"""
Memory services package — Phase 5.1

Re-exports all 12 domain-specific memory engines and the shared
``BaseMemoryEngine`` for the Persistent Project Memory Engine.
"""
from memory.services.base_memory_service import BaseMemoryEngine
from memory.services.project_memory_engine import ProjectMemoryEngine
from memory.services.agent_memory_engine import AgentMemoryEngine
from memory.services.requirement_memory_engine import RequirementMemoryEngine
from memory.services.architecture_memory_engine import ArchitectureMemoryEngine
from memory.services.database_memory_engine import DatabaseMemoryEngine
from memory.services.api_memory_engine import APIMemoryEngine
from memory.services.backend_memory_engine import BackendMemoryEngine
from memory.services.frontend_memory_engine import FrontendMemoryEngine
from memory.services.security_memory_engine import SecurityMemoryEngine
from memory.services.testing_memory_engine import TestingMemoryEngine
from memory.services.deployment_memory_engine import DeploymentMemoryEngine
from memory.services.documentation_memory_engine import DocumentationMemoryEngine

# Convenience mapping: domain name → engine class
ENGINE_REGISTRY = {
    "project": ProjectMemoryEngine,
    "agent": AgentMemoryEngine,
    "requirement": RequirementMemoryEngine,
    "architecture": ArchitectureMemoryEngine,
    "database": DatabaseMemoryEngine,
    "api": APIMemoryEngine,
    "backend": BackendMemoryEngine,
    "frontend": FrontendMemoryEngine,
    "security": SecurityMemoryEngine,
    "testing": TestingMemoryEngine,
    "deployment": DeploymentMemoryEngine,
    "documentation": DocumentationMemoryEngine,
}


def get_engine(domain: str) -> BaseMemoryEngine:
    """
    Resolve a domain name to its memory engine instance.

    Raises:
        ValueError: If the domain is not recognised.
    """
    cls = ENGINE_REGISTRY.get(domain.lower())
    if cls is None:
        raise ValueError(
            f"Unknown memory domain '{domain}'. "
            f"Valid domains: {', '.join(ENGINE_REGISTRY.keys())}"
        )
    return cls()


__all__ = [
    "BaseMemoryEngine",
    "ProjectMemoryEngine",
    "AgentMemoryEngine",
    "RequirementMemoryEngine",
    "ArchitectureMemoryEngine",
    "DatabaseMemoryEngine",
    "APIMemoryEngine",
    "BackendMemoryEngine",
    "FrontendMemoryEngine",
    "SecurityMemoryEngine",
    "TestingMemoryEngine",
    "DeploymentMemoryEngine",
    "DocumentationMemoryEngine",
    "ENGINE_REGISTRY",
    "get_engine",
]
