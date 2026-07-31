"""
ContextAggregator — Phase 5.5

Aggregates 12+ context sources into unified context bundles:
- Project Metadata
- Memory Context
- RAG Results
- Previous Agent Outputs
- Human Inputs
- Timeline Information
- Validation Reports
- Collaboration Reports
- Testing Reports
- Security Reports
- Documentation Reports
- Deployment Reports
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from orchestrator.graph import get_pipeline_state

logger = logging.getLogger(__name__)


class ContextAggregator:
    """
    Context Aggregation System.
    """

    async def aggregate_all_sources(self, project_id: int) -> Dict[str, Any]:
        """
        Aggregate all available context sources into a master context repository dict.
        """
        logger.info(f"[CONTEXT-AGGREGATOR] Aggregating context sources for project {project_id}")

        state = get_pipeline_state(project_id) or {}

        # 1. Previous Agent Outputs & Reports
        pm_output = state.get("project_manager")
        ba_output = state.get("business_analyst")
        po_output = state.get("product_owner")
        sa_output = state.get("solution_architect")
        db_output = state.get("database_engineer")
        api_output = state.get("api_designer")
        be_output = state.get("backend_developer")
        sec_output = state.get("security_engineer")
        qa_output = state.get("qa_engineer")
        fe_output = state.get("frontend_developer")
        cr_output = state.get("code_reviewer")
        doc_output = state.get("documentation_writer")
        devops_output = state.get("devops_engineer")

        # 2. Memory Context
        memory_ctx = None
        try:
            from memory.manager import default_manager
            memory_svc = default_manager.get_service()
            conv = memory_svc.get_conversation_history(project_id, limit=5)
            if conv:
                memory_ctx = {"conversation_history": conv}
        except Exception as exc:
            logger.debug(f"[CONTEXT-AGGREGATOR] Memory retrieval notice: {exc}")

        # 3. RAG Results
        rag_ctx = None
        try:
            from rag.services.context_builder import ContextBuilderService
            from rag.schemas.context import ContextRequest
            rag_builder = ContextBuilderService()
            rag_resp = await rag_builder.build_context(
                ContextRequest(
                    project_id=project_id,
                    agent_name="system",
                    query=f"Aggregated context query for project {project_id}",
                    limit=5,
                )
            )
            if rag_resp and rag_resp.context:
                rag_ctx = {"context_text": rag_resp.context.context_text}
        except Exception as exc:
            logger.debug(f"[CONTEXT-AGGREGATOR] RAG retrieval notice: {exc}")

        # 4. Collaboration Reports
        collab_ctx = None
        try:
            from collaboration.services.analytics_service import AnalyticsService
            analytics = AnalyticsService()
            collab_report = await analytics.get_collaboration_report(project_id)
            collab_ctx = collab_report.model_dump()
        except Exception as exc:
            logger.debug(f"[CONTEXT-AGGREGATOR] Collaboration report notice: {exc}")

        return {
            "Project": {"project_id": project_id, "idea": state.get("project_idea")},
            "Requirement": ba_output or pm_output,
            "Architecture": sa_output,
            "Memory": memory_ctx,
            "RAG": rag_ctx,
            "Human Approval": {"status": state.get("approval_status")},
            "Workflow": {"current_agent": state.get("current_agent")},
            "Timeline": {"milestones": (pm_output or {}).get("milestones")},
            "Validation": cr_output,
            "Security": sec_output,
            "Testing": qa_output,
            "Documentation": doc_output,
            "Deployment": devops_output,
            "Generated Files": fe_output or be_output,
            "Frontend": fe_output,
            "Backend": be_output,
            "Database": db_output,
            "API": api_output,
            "Collaboration": collab_ctx,
        }
