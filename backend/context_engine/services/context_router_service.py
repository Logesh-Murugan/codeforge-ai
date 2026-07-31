"""
ContextRouterService — Phase 5.5

Intelligent Context Router.
Routes required context subsets to agents based on domain rules.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ContextRouterService:
    """
    Intelligent Context Router.
    """

    # Agent-Specific Routing Matrix
    ROUTING_MATRIX: Dict[str, List[str]] = {
        "project_manager": ["Project", "Memory", "Human Approval", "Workflow", "Timeline"],
        "business_analyst": ["Project", "Memory", "Human Approval", "RAG", "Requirement"],
        "product_owner": ["Requirement", "Memory", "Human Approval", "Timeline"],
        "solution_architect": ["Requirement", "Memory", "Validation", "Timeline", "Architecture"],
        "database_engineer": ["Architecture", "Memory", "Database", "Validation"],
        "api_designer": ["Architecture", "Database", "Memory", "API", "Validation"],
        "backend_developer": ["Architecture", "API", "Database", "Security", "Testing", "Memory", "RAG", "Backend"],
        "frontend_developer": ["Frontend", "API", "Memory", "Validation"],
        "security_engineer": ["Architecture", "Backend", "API", "Testing", "Security"],
        "qa_engineer": ["Testing", "API", "Security", "Backend", "Validation"],
        "code_reviewer": ["Backend", "Frontend", "Architecture", "Security", "Testing", "Validation"],
        "documentation_writer": ["Architecture", "API", "Database", "Backend", "Frontend", "Documentation"],
        "devops_engineer": ["Architecture", "Backend", "Frontend", "Deployment", "Export"],
    }

    async def route_context_for_agent(
        self, project_id: int, target_agent: str, master_bundle: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Filter master context bundle down to ONLY the contexts required by `target_agent`.
        """
        logger.info(f"[CONTEXT-ROUTER] Routing context for agent '{target_agent}' project {project_id}")

        allowed_types = self.ROUTING_MATRIX.get(target_agent)
        if not allowed_types:
            # Default fallback: return all available non-null keys
            return {k: v for k, v in master_bundle.items() if v is not None}

        routed: Dict[str, Any] = {}
        for req_type in allowed_types:
            if req_type in master_bundle and master_bundle[req_type] is not None:
                routed[req_type] = master_bundle[req_type]

        return routed
