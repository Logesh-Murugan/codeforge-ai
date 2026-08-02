"""
Verification Suite — Phase 5.10 Portfolio Output System
"""
import asyncio
import sys

from portfolio.config import portfolio_settings
from portfolio.schemas.portfolio_schema import PortfolioDTO
from portfolio.services.portfolio_service import portfolio_service
from portfolio.services.metrics_service import metrics_service
from portfolio.services.diagram_service import diagram_service
from portfolio.services.portfolio_bundle_service import portfolio_bundle_service
from portfolio.generators.markdown_generator import markdown_generator
from portfolio.generators.html_generator import html_generator
from portfolio.generators.json_generator import json_generator
from portfolio.generators.pdf_metadata_generator import pdf_metadata_generator


async def run_all_tests():
    print("--- 1. Testing Portfolio Settings ---")
    assert portfolio_settings.ENABLE_MERMAID_DIAGRAMS is True
    print("Config tests PASSED [OK]")

    print("\n--- 2. Testing Metrics & Diagram Services ---")
    metrics = await metrics_service.calculate_metrics(project_id=1)
    assert metrics.lines_of_code == 3450
    assert metrics.quality_grade == "A+"

    diagrams = await diagram_service.generate_diagrams(project_id=1)
    assert "graph TD" in diagrams.flowchart
    assert "sequenceDiagram" in diagrams.sequence_diagram
    assert "erDiagram" in diagrams.entity_relationship_diagram
    print("Metrics & Diagram tests PASSED [OK]")

    print("\n--- 3. Testing PortfolioService Facade ---")
    pf = await portfolio_service.get_portfolio(project_id=1)
    assert pf.project_id == 1
    assert len(pf.agent_workflows) == 13
    assert len(pf.downloads) >= 1
    print("PortfolioService tests PASSED [OK]")

    print("\n--- 4. Testing Multi-Format Generators (MD, HTML, JSON, PDF Meta) ---")
    md = markdown_generator.generate_markdown(pf)
    html = html_generator.generate_html(pf)
    json_str = json_generator.generate_json(pf)
    pdf_meta = pdf_metadata_generator.generate_pdf_metadata(pf)

    assert "# Engineering Portfolio" in md
    assert "<!DOCTYPE html>" in html
    assert '"project_id": 1' in json_str
    assert pdf_meta["project_id"] == 1
    print("Generators tests PASSED [OK]")

    print("\n--- 5. Testing ZIP Portfolio Package Bundler ---")
    zip_bytes = await portfolio_bundle_service.create_portfolio_bundle_zip(pf)
    assert len(zip_bytes) > 0
    print("ZIP Portfolio Package Bundler tests PASSED [OK]")

    print("\n==========================================")
    print("ALL PHASE 5.10 PORTFOLIO TESTS PASSED SUCCESSFULLY! [OK]")
    print("==========================================")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
