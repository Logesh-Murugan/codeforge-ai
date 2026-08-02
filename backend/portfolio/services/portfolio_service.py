"""
PortfolioService — Phase 5.10

Main Portfolio Service Facade.
"""
from __future__ import annotations

import logging
from portfolio.schemas.portfolio_schema import DownloadArtifactDTO, PortfolioDTO
from portfolio.services.architecture_service import architecture_service
from portfolio.services.diagram_service import diagram_service
from portfolio.services.metrics_service import metrics_service
from portfolio.services.workflow_service import workflow_service

logger = logging.getLogger(__name__)


class PortfolioService:
    """
    Main Portfolio Service Facade.
    """

    async def get_portfolio(self, project_id: int) -> PortfolioDTO:
        """Assemble full portfolio package for project_id."""
        metrics = await metrics_service.calculate_metrics(project_id)
        arch = await architecture_service.get_architecture_docs(project_id)
        workflows = await workflow_service.get_agent_workflows(project_id)
        diagrams = await diagram_service.generate_diagrams(project_id)

        downloads = [
            DownloadArtifactDTO(artifact_name="Complete Portfolio Package", file_type="ZIP", download_url=f"/portfolio/download/{project_id}?format=zip", file_size_kb=450.0),
            DownloadArtifactDTO(artifact_name="Executive Portfolio Report", file_type="Markdown", download_url=f"/portfolio/reports/{project_id}?format=md", file_size_kb=25.0),
            DownloadArtifactDTO(artifact_name="Interactive Portfolio Webpage", file_type="HTML", download_url=f"/portfolio/reports/{project_id}?format=html", file_size_kb=35.0),
            DownloadArtifactDTO(artifact_name="Portfolio JSON Telemetry Data", file_type="JSON", download_url=f"/portfolio/reports/{project_id}?format=json", file_size_kb=15.0),
        ]

        return PortfolioDTO(
            project_id=project_id,
            project_name=f"Generated AI Project #{project_id}",
            executive_summary="Production-grade full-stack web application built by CodeForge AI's 13-Agent Orchestrator with 100% automated quality gate validation.",
            project_vision="Transform natural language requirements into downloadable, validated software artifacts.",
            problem_statement="Automate software development lifecycle with strict architectural standards, security auditing, and zero human intervention.",
            objectives=[
                "Implement modular controller-service-repository architecture",
                "Pass all 12-stage validation quality gates with A+ grade",
                "Provide multi-agent telemetry and interactive visual workflow",
            ],
            technology_stack=["FastAPI", "Python 3.11", "SQLAlchemy 2.0", "Pydantic V2", "React", "Next.js 14", "Tailwind CSS", "Docker", "ChromaDB"],
            metrics=metrics,
            agent_workflows=workflows,
            architecture=arch,
            diagrams=diagrams,
            downloads=downloads,
        )


portfolio_service = PortfolioService()
