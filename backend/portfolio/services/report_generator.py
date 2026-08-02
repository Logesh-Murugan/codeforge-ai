"""
Report Generator — Phase 5.10

Aggregates all portfolio reports.
"""
from __future__ import annotations

import logging
from typing import Dict
from portfolio.generators.html_generator import html_generator
from portfolio.generators.json_generator import json_generator
from portfolio.generators.markdown_generator import markdown_generator
from portfolio.generators.pdf_metadata_generator import pdf_metadata_generator
from portfolio.schemas.portfolio_schema import PortfolioDTO

logger = logging.getLogger(__name__)


class PortfolioReportAggregator:
    """
    Portfolio Report Aggregator Service.
    """

    def generate_all_reports(self, portfolio: PortfolioDTO) -> Dict[str, str]:
        """Aggregate Markdown, HTML, JSON, and PDF Metadata reports."""
        return {
            "portfolio.md": markdown_generator.generate_markdown(portfolio),
            "portfolio.html": html_generator.generate_html(portfolio),
            "portfolio.json": json_generator.generate_json(portfolio),
            "pdf_metadata.json": str(pdf_metadata_generator.generate_pdf_metadata(portfolio)),
        }


report_aggregator = PortfolioReportAggregator()
