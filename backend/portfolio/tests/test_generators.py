"""
Generators Tests — Phase 5.10
"""
import pytest
from portfolio.generators.html_generator import html_generator
from portfolio.generators.json_generator import json_generator
from portfolio.generators.markdown_generator import markdown_generator
from portfolio.generators.pdf_metadata_generator import pdf_metadata_generator
from portfolio.services.portfolio_service import portfolio_service


@pytest.mark.asyncio
async def test_generators():
    pf = await portfolio_service.get_portfolio(project_id=1)
    md = markdown_generator.generate_markdown(pf)
    html = html_generator.generate_html(pf)
    json_str = json_generator.generate_json(pf)
    pdf_meta = pdf_metadata_generator.generate_pdf_metadata(pf)

    assert "# Engineering Portfolio" in md
    assert "<!DOCTYPE html>" in html
    assert '"project_id": 1' in json_str
    assert pdf_meta["project_id"] == 1
