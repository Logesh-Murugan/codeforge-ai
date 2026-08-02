"""
JSON Portfolio Generator — Phase 5.10
"""
from __future__ import annotations

import logging
from portfolio.schemas.portfolio_schema import PortfolioDTO

logger = logging.getLogger(__name__)


class JsonGenerator:
    """
    JSON Portfolio Exporter.
    """

    def generate_json(self, portfolio: PortfolioDTO) -> str:
        """Export machine-readable JSON portfolio string."""
        return portfolio.model_dump_json(indent=2)


json_generator = JsonGenerator()
