"""
ContextOrchestrator — Phase 5.5

9-stage Context Orchestration Pipeline:
Context Preparation
↓
Context Aggregation
↓
Context Validation
↓
Context Routing
↓
Context Scoring
↓
Context Distribution
↓
Context Consumption
↓
Context Logging
↓
Context Visualization
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from context_engine.aggregators.context_aggregator import ContextAggregator
from context_engine.managers.context_history_manager import ContextHistoryManager
from context_engine.services.context_router_service import ContextRouterService
from context_engine.services.context_scoring_service import ContextScoringService
from context_engine.validators.context_validator import ContextValidator
from context_engine.visualization.flow_generator import ContextFlowGenerator

logger = logging.getLogger(__name__)


class ContextOrchestrator:
    """
    Context Orchestrator System.
    """

    def __init__(self) -> None:
        self.aggregator = ContextAggregator()
        self.validator = ContextValidator()
        self.router = ContextRouterService()
        self.scorer = ContextScoringService()
        self.history_manager = ContextHistoryManager()
        self.visualizer = ContextFlowGenerator()

    async def orchestrate_context_flow(
        self, project_id: int, target_agent: str
    ) -> Dict[str, Any]:
        """
        Run the complete 9-stage context orchestration pipeline for `target_agent`.
        """
        logger.info(
            f"[CONTEXT-ORCHESTRATOR] Starting 9-stage context flow for agent '{target_agent}' project {project_id}"
        )

        # Stage 1: Context Preparation
        prep_status = {"prepared": True, "project_id": project_id, "agent": target_agent}

        # Stage 2: Context Aggregation
        aggregated_bundle = await self.aggregator.aggregate_all_sources(project_id)

        # Stage 3: Context Validation
        validation_res = await self.validator.validate_bundle(
            project_id=project_id, target_agent=target_agent, bundle=aggregated_bundle
        )

        # Stage 4: Context Routing
        routed_bundle = await self.router.route_context_for_agent(
            project_id=project_id, target_agent=target_agent, master_bundle=aggregated_bundle
        )

        # Stage 5: Context Scoring
        quality_score = await self.scorer.evaluate_context_quality(
            project_id=project_id, context_bundle=routed_bundle
        )

        # Stage 6: Context Distribution
        distributed_bundle = {
            "project_id": project_id,
            "target_agent": target_agent,
            "contexts": routed_bundle,
            "quality_score": quality_score.overall_quality_score,
        }

        # Stage 7: Context Consumption (ready for agent execution)

        # Stage 8: Context Logging
        await self.history_manager.log_event(
            project_id=project_id,
            context_type="Bundle",
            producer_agent="context_orchestrator",
            consumer_agent=target_agent,
            action="routed",
            change_summary=f"Routed {len(routed_bundle)} context types to {target_agent}.",
        )

        # Stage 9: Context Visualization Data Generation
        vis_data = await self.visualizer.generate_visualization_data(project_id)

        return {
            "project_id": project_id,
            "target_agent": target_agent,
            "routed_bundle": routed_bundle,
            "validation": validation_res.model_dump(),
            "quality_score": quality_score.model_dump(),
            "visualization": vis_data.model_dump(),
        }
