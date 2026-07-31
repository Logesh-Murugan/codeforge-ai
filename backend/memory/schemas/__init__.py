"""
Memory schemas package — Phase 5.1

Re-exports all domain-specific Pydantic schemas for the Persistent
Project Memory Engine, plus backward-compatible re-exports from the
original ``schemas_core`` module (formerly ``schemas.py``).
"""
# ── Backward-compatible re-exports from the original schemas module ─────
# The original memory/schemas.py was renamed to memory/schemas_core.py to
# avoid a namespace collision with this package directory.  All the symbols
# that existing code imports via ``from memory.schemas import X`` are
# re-exported here so every import path continues to work.
from memory.schemas_core import (
    AgentContext,
    ArtifactType,
    CollectionName,
    EmbeddingProviderName,
    MemoryMetadata,
    MemoryMode,
    MemoryQuery,
    MemoryQueryResult,
    MemoryRecord,
    MemoryStoreRequest,
    ProjectHistoryEntry,
    ProviderHealth,
    TextChunk,
    # Phase 3.4
    AgentMemoryRecord,
    GeneratedFileRecord,
    RevisionEntry,
    ProjectSnapshot,
    StoreArtifactRequest,
    StoreRevisionRequest,
    VersionHistoryQuery,
    MemorySearchRequest,
)
from memory.schemas.project import (
    ProjectMemoryCreate,
    ProjectMemoryUpdate,
    ProjectMemoryResponse,
    ProjectMemorySearchResult,
)
from memory.schemas.agent import (
    AgentMemoryCreate,
    AgentMemoryUpdate,
    AgentMemoryResponse,
    AgentMemorySearchResult,
)
from memory.schemas.requirement import (
    RequirementMemoryCreate,
    RequirementMemoryUpdate,
    RequirementMemoryResponse,
    RequirementMemorySearchResult,
)
from memory.schemas.architecture import (
    ArchitectureMemoryCreate,
    ArchitectureMemoryUpdate,
    ArchitectureMemoryResponse,
    ArchitectureMemorySearchResult,
)
from memory.schemas.database import (
    DatabaseMemoryCreate,
    DatabaseMemoryUpdate,
    DatabaseMemoryResponse,
    DatabaseMemorySearchResult,
)
from memory.schemas.api import (
    APIMemoryCreate,
    APIMemoryUpdate,
    APIMemoryResponse,
    APIMemorySearchResult,
)
from memory.schemas.backend import (
    BackendMemoryCreate,
    BackendMemoryUpdate,
    BackendMemoryResponse,
    BackendMemorySearchResult,
)
from memory.schemas.frontend import (
    FrontendMemoryCreate,
    FrontendMemoryUpdate,
    FrontendMemoryResponse,
    FrontendMemorySearchResult,
)
from memory.schemas.security import (
    SecurityMemoryCreate,
    SecurityMemoryUpdate,
    SecurityMemoryResponse,
    SecurityMemorySearchResult,
)
from memory.schemas.testing import (
    TestingMemoryCreate,
    TestingMemoryUpdate,
    TestingMemoryResponse,
    TestingMemorySearchResult,
)
from memory.schemas.deployment import (
    DeploymentMemoryCreate,
    DeploymentMemoryUpdate,
    DeploymentMemoryResponse,
    DeploymentMemorySearchResult,
)
from memory.schemas.documentation import (
    DocumentationMemoryCreate,
    DocumentationMemoryUpdate,
    DocumentationMemoryResponse,
    DocumentationMemorySearchResult,
)

__all__ = [
    # ── Core schemas (backward-compat from schemas_core.py) ──
    "AgentContext", "ArtifactType", "CollectionName",
    "EmbeddingProviderName", "MemoryMetadata", "MemoryMode",
    "MemoryQuery", "MemoryQueryResult", "MemoryRecord",
    "MemoryStoreRequest", "ProjectHistoryEntry", "ProviderHealth",
    "TextChunk", "AgentMemoryRecord", "GeneratedFileRecord",
    "RevisionEntry", "ProjectSnapshot", "StoreArtifactRequest",
    "StoreRevisionRequest", "VersionHistoryQuery", "MemorySearchRequest",
    # ── Phase 5.1 domain schemas ──
    # Project
    "ProjectMemoryCreate", "ProjectMemoryUpdate",
    "ProjectMemoryResponse", "ProjectMemorySearchResult",
    # Agent
    "AgentMemoryCreate", "AgentMemoryUpdate",
    "AgentMemoryResponse", "AgentMemorySearchResult",
    # Requirement
    "RequirementMemoryCreate", "RequirementMemoryUpdate",
    "RequirementMemoryResponse", "RequirementMemorySearchResult",
    # Architecture
    "ArchitectureMemoryCreate", "ArchitectureMemoryUpdate",
    "ArchitectureMemoryResponse", "ArchitectureMemorySearchResult",
    # Database
    "DatabaseMemoryCreate", "DatabaseMemoryUpdate",
    "DatabaseMemoryResponse", "DatabaseMemorySearchResult",
    # API
    "APIMemoryCreate", "APIMemoryUpdate",
    "APIMemoryResponse", "APIMemorySearchResult",
    # Backend
    "BackendMemoryCreate", "BackendMemoryUpdate",
    "BackendMemoryResponse", "BackendMemorySearchResult",
    # Frontend
    "FrontendMemoryCreate", "FrontendMemoryUpdate",
    "FrontendMemoryResponse", "FrontendMemorySearchResult",
    # Security
    "SecurityMemoryCreate", "SecurityMemoryUpdate",
    "SecurityMemoryResponse", "SecurityMemorySearchResult",
    # Testing
    "TestingMemoryCreate", "TestingMemoryUpdate",
    "TestingMemoryResponse", "TestingMemorySearchResult",
    # Deployment
    "DeploymentMemoryCreate", "DeploymentMemoryUpdate",
    "DeploymentMemoryResponse", "DeploymentMemorySearchResult",
    # Documentation
    "DocumentationMemoryCreate", "DocumentationMemoryUpdate",
    "DocumentationMemoryResponse", "DocumentationMemorySearchResult",
]

