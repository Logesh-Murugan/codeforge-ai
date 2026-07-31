"""
ContextFlowGenerator — Phase 5.5

Generates context dependency flow graphs, visual edge connections, nodes, and timelines.
"""
from __future__ import annotations

import logging
from typing import List

from context_engine.config import context_settings
from context_engine.schemas.analytics import (
    ContextFlowGraphEdge,
    ContextFlowGraphNode,
    ContextVisualizationResponse,
)

logger = logging.getLogger(__name__)


class ContextFlowGenerator:
    """
    Context Visualization System generator.
    """

    async def generate_visualization_data(
        self, project_id: int
    ) -> ContextVisualizationResponse:
        """
        Generate flow graph nodes and edges for frontend context graph rendering.
        """
        types = context_settings.ALL_CONTEXT_TYPES

        nodes: List[ContextFlowGraphNode] = [
            ContextFlowGraphNode(
                id=t.lower().replace(" ", "_"),
                label=t,
                context_type=t,
                status="valid",
            )
            for t in types
        ]

        edges: List[ContextFlowGraphEdge] = [
            ContextFlowGraphEdge(source="project", target="requirement", label="defines"),
            ContextFlowGraphEdge(source="requirement", target="architecture", label="shapes"),
            ContextFlowGraphEdge(source="architecture", target="database", label="structures"),
            ContextFlowGraphEdge(source="architecture", target="api", label="specifies"),
            ContextFlowGraphEdge(source="database", target="backend", label="provides_schema"),
            ContextFlowGraphEdge(source="api", target="backend", label="contracts"),
            ContextFlowGraphEdge(source="api", target="frontend", label="exposes_endpoints"),
            ContextFlowGraphEdge(source="backend", target="security", label="audit_target"),
            ContextFlowGraphEdge(source="backend", target="testing", label="test_target"),
            ContextFlowGraphEdge(source="security", target="qa", label="validates"),
            ContextFlowGraphEdge(source="testing", target="code_reviewer", label="verifies"),
            ContextFlowGraphEdge(source="documentation", target="devops", label="deploys"),
        ]

        return ContextVisualizationResponse(
            project_id=project_id,
            nodes=nodes,
            edges=edges,
            active_contexts_count=len(nodes),
        )
