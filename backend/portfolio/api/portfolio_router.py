"""
Portfolio Router — Phase 5.10

FastAPI route handlers for Portfolio Output System.

Endpoints:
    GET /portfolio/{project_id}               Full portfolio payload
    GET /portfolio/metrics/{project_id}       Detailed engineering metrics breakdown
    GET /portfolio/reports/{project_id}       Multi-format reports (MD, HTML, JSON, PDF Meta)
    GET /portfolio/download/{project_id}      Download complete portfolio package (ZIP)
    GET /portfolio/architecture/{project_id}  Architecture documentation & Mermaid diagrams
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.security import get_current_user
from portfolio.schemas.portfolio_schema import ArchitectureDocsDTO, EngineeringMetricsDTO, PortfolioDTO
from portfolio.services.architecture_service import architecture_service
from portfolio.services.metrics_service import metrics_service
from portfolio.services.portfolio_bundle_service import portfolio_bundle_service
from portfolio.services.portfolio_service import portfolio_service
from portfolio.services.report_generator import report_aggregator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/portfolio", tags=["portfolio-output"])


@router.get(
    "/{project_id}",
    response_model=PortfolioDTO,
    summary="Get complete portfolio package for project_id",
)
async def get_portfolio_package(
    project_id: int,
    _user=Depends(get_current_user),
):
    """Retrieve full portfolio payload for project_id."""
    return await portfolio_service.get_portfolio(project_id)


@router.get(
    "/metrics/{project_id}",
    response_model=EngineeringMetricsDTO,
    summary="Get detailed engineering metrics breakdown",
)
async def get_portfolio_metrics(
    project_id: int,
    _user=Depends(get_current_user),
):
    """Retrieve engineering metrics for project_id."""
    return await metrics_service.calculate_metrics(project_id)


@router.get(
    "/reports/{project_id}",
    summary="Get multi-format portfolio reports (MD, HTML, JSON, PDF Metadata)",
)
async def get_portfolio_reports(
    project_id: int,
    format: str = "md",
    _user=Depends(get_current_user),
):
    """Retrieve portfolio reports in Markdown, HTML, or JSON format."""
    portfolio = await portfolio_service.get_portfolio(project_id)
    reports = report_aggregator.generate_all_reports(portfolio)
    key = f"portfolio.{format.lower()}"
    content = reports.get(key, reports.get("portfolio.md", ""))
    return {"project_id": project_id, "format": format, "content": content}


@router.get(
    "/download/{project_id}",
    summary="Download complete portfolio package (ZIP)",
)
async def download_portfolio_bundle(
    project_id: int,
    _user=Depends(get_current_user),
):
    """Download bundled portfolio package as a ZIP archive."""
    portfolio = await portfolio_service.get_portfolio(project_id)
    zip_bytes = await portfolio_bundle_service.create_portfolio_bundle_zip(portfolio)

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=portfolio_project_{project_id}.zip"},
    )


@router.get(
    "/architecture/{project_id}",
    response_model=ArchitectureDocsDTO,
    summary="Get architecture documentation & Mermaid diagrams",
)
async def get_portfolio_architecture(
    project_id: int,
    _user=Depends(get_current_user),
):
    """Retrieve architecture documentation for project_id."""
    return await architecture_service.get_architecture_docs(project_id)
