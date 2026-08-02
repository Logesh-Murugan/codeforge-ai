"""
HTML Portfolio Generator — Phase 5.10
"""
from __future__ import annotations

import logging
from portfolio.schemas.portfolio_schema import PortfolioDTO

logger = logging.getLogger(__name__)


class HtmlGenerator:
    """
    HTML Portfolio Page Generator.
    """

    def generate_html(self, portfolio: PortfolioDTO) -> str:
        """Generate responsive HTML portfolio page."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Engineering Portfolio - Project #{portfolio.project_id}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 40px; }}
    .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 24px; margin-bottom: 24px; }}
    h1, h2, h3 {{ color: #38bdf8; }}
    .badge {{ background: #0284c7; color: #fff; padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: bold; }}
  </style>
</head>
<body>
  <div className="card">
    <h1>Engineering Portfolio: {portfolio.project_name} <span className="badge">{portfolio.metrics.quality_grade}</span></h1>
    <p><strong>Executive Summary:</strong> {portfolio.executive_summary}</p>
  </div>
  <div className="card">
    <h2>Engineering Metrics</h2>
    <ul>
      <li>Lines of Code: {portfolio.metrics.lines_of_code}</li>
      <li>Files Generated: {portfolio.metrics.number_of_files}</li>
      <li>Validation Score: {portfolio.metrics.validation_score}/100</li>
      <li>Test Coverage: {portfolio.metrics.test_coverage_pct}%</li>
    </ul>
  </div>
</body>
</html>"""


html_generator = HtmlGenerator()
