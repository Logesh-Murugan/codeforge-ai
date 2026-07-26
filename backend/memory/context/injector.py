"""
ContextInjector — Phase 3.5

Builds rich, role-aware prompt blocks for every agent in the pipeline.

Each agent role is associated with:
  - A list of ChromaDB collections relevant to its work.
  - A query template that drives semantic retrieval.

Usage
-----
    injector = ContextInjector(memory_service=svc)
    block = injector.build_context_block(
        project_id=1,
        agent_name="backend_developer",
        user_query="implement JWT authentication",
        limit=5,
    )
    prompt = system_prompt + "\\n\\n" + block
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from memory.schemas import AgentContext, MemoryQueryResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Agent role registry
# ---------------------------------------------------------------------------

@dataclass
class AgentRole:
    """
    Describes one agent's memory-reading profile.

    Attributes:
        name:           Canonical agent identifier (matches agent_name in metadata).
        collections:    ChromaDB collections this agent reads for context.
        query_template: ``{query}`` is substituted at call time.
        description:    Human-readable description of the role.
    """
    name: str
    collections: List[str]
    query_template: str = "{query}"
    description: str = ""


# Default role definitions — all pipeline agents
AGENT_ROLES: Dict[str, AgentRole] = {
    "requirements_analyst": AgentRole(
        name="requirements_analyst",
        collections=["requirements", "conversation", "project_history"],
        query_template="Requirements and user stories related to: {query}",
        description="Gathers and refines project requirements.",
    ),
    "architect": AgentRole(
        name="architect",
        collections=["requirements", "architecture", "database_design", "api_contracts"],
        query_template="Architecture decisions and system design for: {query}",
        description="Designs system architecture and data models.",
    ),
    "api_designer": AgentRole(
        name="api_designer",
        collections=["requirements", "architecture", "api_contracts"],
        query_template="API endpoints, contracts, and REST design for: {query}",
        description="Designs REST/GraphQL API contracts.",
    ),
    "backend_developer": AgentRole(
        name="backend_developer",
        collections=["requirements", "architecture", "api_contracts", "backend_code", "database_design"],
        query_template="Backend implementation details and code patterns for: {query}",
        description="Implements backend services and business logic.",
    ),
    "frontend_developer": AgentRole(
        name="frontend_developer",
        collections=["requirements", "api_contracts", "frontend_code", "architecture"],
        query_template="Frontend components, UI patterns, and API usage for: {query}",
        description="Implements frontend components and pages.",
    ),
    "security_engineer": AgentRole(
        name="security_engineer",
        collections=["requirements", "backend_code", "frontend_code", "api_contracts", "security_reports"],
        query_template="Security vulnerabilities, authentication, and hardening for: {query}",
        description="Reviews and hardens the application for security.",
    ),
    "qa_engineer": AgentRole(
        name="qa_engineer",
        collections=["requirements", "backend_code", "frontend_code", "api_contracts", "qa_reports"],
        query_template="Test cases, test coverage, and quality metrics for: {query}",
        description="Designs and executes quality assurance.",
    ),
    "devops_engineer": AgentRole(
        name="devops_engineer",
        collections=["architecture", "backend_code", "frontend_code", "devops", "documentation"],
        query_template="Deployment, infrastructure, and CI/CD for: {query}",
        description="Sets up deployment pipelines and infrastructure.",
    ),
    "documentation_writer": AgentRole(
        name="documentation_writer",
        collections=["requirements", "architecture", "api_contracts", "documentation", "backend_code"],
        query_template="Documentation, API specs, and usage guides for: {query}",
        description="Generates user and developer documentation.",
    ),
}


class ContextInjector:
    """
    Builds role-aware context blocks for agent prompts.

    Args:
        memory_service: Injected :class:`~memory.service.MemoryService`.
                        Falls back to the default auto-wired service.
        extra_roles:    Optional dict of additional :class:`AgentRole` entries
                        merged on top of :data:`AGENT_ROLES`.
    """

    def __init__(
        self,
        memory_service=None,
        extra_roles: Optional[Dict[str, AgentRole]] = None,
    ) -> None:
        if memory_service is None:
            from memory.manager import default_manager
            memory_service = default_manager.get_service()
        self._svc = memory_service
        self._roles: Dict[str, AgentRole] = dict(AGENT_ROLES)
        if extra_roles:
            self._roles.update(extra_roles)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_role(self, agent_name: str) -> AgentRole:
        """Return the AgentRole for *agent_name*, creating a generic one if unknown."""
        if agent_name in self._roles:
            return self._roles[agent_name]
        # Generic fallback: search all domain collections
        logger.debug("[INJECTOR] Unknown agent '%s' — using generic role", agent_name)
        return AgentRole(
            name=agent_name,
            collections=["requirements", "architecture", "backend_code", "frontend_code"],
            description="Generic agent role.",
        )

    def build_context(
        self,
        project_id: int,
        agent_name: str,
        user_query: str,
        limit: int = 5,
        threshold: float = 0.0,
        extra_collections: Optional[List[str]] = None,
    ) -> AgentContext:
        """
        Retrieve relevant memory and assemble an :class:`AgentContext`.

        Args:
            project_id:        Owning project.
            agent_name:        The agent requesting context.
            user_query:        The current task description / question.
            limit:             Max chunks to include in total.
            threshold:         Min similarity score for chunks.
            extra_collections: Additional collections to search on top of
                               the role's default set.

        Returns:
            :class:`~memory.schemas.AgentContext`
        """
        role = self.get_role(agent_name)
        collections = list(role.collections)
        if extra_collections:
            for col in extra_collections:
                if col not in collections:
                    collections.append(col)

        # Expand the query using the role template
        expanded_query = role.query_template.format(query=user_query)

        return self._svc.build_agent_context(
            project_id=project_id,
            agent_name=agent_name,
            query=expanded_query,
            collections=collections,
            limit=limit,
            threshold=threshold,
        )

    def build_context_block(
        self,
        project_id: int,
        agent_name: str,
        user_query: str,
        limit: int = 5,
        threshold: float = 0.0,
    ) -> str:
        """
        Convenience wrapper: build context and render it as a prompt string.

        Returns:
            Markdown-formatted string ready to append to a prompt.
        """
        ctx = self.build_context(
            project_id=project_id,
            agent_name=agent_name,
            user_query=user_query,
            limit=limit,
            threshold=threshold,
        )
        return ctx.to_prompt_block()

    def register_role(self, role: AgentRole) -> None:
        """Register (or replace) an :class:`AgentRole` at runtime."""
        self._roles[role.name] = role
        logger.debug("[INJECTOR] Registered role '%s'", role.name)

    @property
    def available_roles(self) -> List[str]:
        """Names of all currently registered agent roles."""
        return list(self._roles.keys())
