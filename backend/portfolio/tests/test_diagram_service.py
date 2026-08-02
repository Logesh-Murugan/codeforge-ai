"""
DiagramService Tests — Phase 5.10
"""
import pytest
from portfolio.services.diagram_service import diagram_service


@pytest.mark.asyncio
async def test_generate_diagrams():
    diagrams = await diagram_service.generate_diagrams(project_id=1)
    assert "graph" in diagrams.flowchart
    assert "sequenceDiagram" in diagrams.sequence_diagram
    assert "erDiagram" in diagrams.entity_relationship_diagram
    assert "classDiagram" in diagrams.class_diagram
