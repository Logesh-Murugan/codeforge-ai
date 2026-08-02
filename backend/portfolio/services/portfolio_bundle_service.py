"""
PortfolioBundleService — Phase 5.10

Bundles reports, diagrams, metrics into downloadable ZIP package.
"""
from __future__ import annotations

import io
import logging
import zipfile
from typing import Dict
from portfolio.schemas.portfolio_schema import PortfolioDTO
from portfolio.services.report_generator import report_aggregator

logger = logging.getLogger(__name__)


class PortfolioBundleService:
    """
    ZIP Portfolio Package Bundler.
    """

    async def create_portfolio_bundle_zip(self, portfolio: PortfolioDTO) -> bytes:
        """Create in-memory ZIP package containing all portfolio artifacts."""
        reports = report_aggregator.generate_all_reports(portfolio)
        buffer = io.BytesIO()

        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for name, content in reports.items():
                zf.writestr(f"portfolio_reports/{name}", content)

            # Write Mermaid Diagrams
            diagrams = portfolio.diagrams.model_dump()
            for diag_name, diag_src in diagrams.items():
                zf.writestr(f"diagrams/{diag_name}.mmd", diag_src)

        return buffer.getvalue()


portfolio_bundle_service = PortfolioBundleService()
