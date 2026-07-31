"""
ContextExchangeService — Phase 5.4

Aggregates requirements, architecture designs, database schemas, API specifications,
security recommendations, QA recommendations, memory context, and RAG context
for any target agent before execution.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from collaboration.schemas.communication import ContextBundleResponse
from orchestrator.graph import get_pipeline_state

logger = logging.getLogger(__name__)


class ContextExchangeService:
    """
    Service responsible for assembling rich multi-agent context bundles.
    """

    async def assemble_context_bundle(
        self, project_id: int, target_agent: str
    ) -> ContextBundleResponse:
        """
        Assemble all upstream context required by `target_agent`.
        For example, Backend Developer receives:
        - Requirements documents (business_analyst / product_owner)
        - Architecture designs (solution_architect)
        - Database schemas (database_engineer)
        - API specifications (api_designer)
        - Security recommendations (security_engineer)
        - QA recommendations (qa_engineer)
        - Memory & RAG context
        """
        logger.info(
            f"[COLLABORATION-CONTEXT] Assembling context bundle for target_agent='{target_agent}' project={project_id}"
        )

        state = get_pipeline_state(project_id) or {}

        # Extract agent output dictionaries from graph state
        requirements = state.get("business_analyst") or state.get("project_manager")
        architecture = state.get("solution_architect")
        db_schema = state.get("database_engineer")
        api_spec = state.get("api_designer")
        security_recs = state.get("security_engineer")
        qa_recs = state.get("qa_engineer")

        # Fetch Memory & RAG context if memory service is available
        memory_ctx: Optional[Dict[str, Any]] = None
        rag_ctx: Optional[Dict[str, Any]] = None

        try:
            from memory.manager import default_manager
            memory_svc = default_manager.get_service()
            conv = memory_svc.get_conversation_history(project_id, limit=5)
            if conv:
                memory_ctx = {"conversation_history": conv}
        except Exception as exc:
            logger.debug(f"[COLLABORATION-CONTEXT] Memory context retrieval notice: {exc}")

        try:
            from rag.services.context_builder import ContextBuilderService
            from rag.schemas.context import ContextRequest
            rag_builder = ContextBuilderService()
            rag_resp = await rag_builder.build_context(
                ContextRequest(
                    project_id=project_id,
                    agent_name=target_agent,
                    query=f"Context dependencies for {target_agent}",
                    limit=5,
                )
            )
            if rag_resp and rag_resp.context:
                rag_ctx = {
                    "formatted_text": rag_resp.context.context_text,
                    "chunk_count": rag_resp.total_chunks,
                }
        except Exception as exc:
            logger.debug(f"[COLLABORATION-CONTEXT] RAG context retrieval notice: {exc}")

        return ContextBundleResponse(
            project_id=project_id,
            target_agent=target_agent,
            requirements=requirements,
            architecture=architecture,
            db_schema=db_schema,
            api_spec=api_spec,
            security_recommendations=security_recs,
            qa_recommendations=qa_recs,
            memory_context=memory_ctx,
            rag_context=rag_ctx,
        )
