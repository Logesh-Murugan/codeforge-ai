"""
Markdown Portfolio Generator — Phase 5.10
"""
from __future__ import annotations

import logging
from typing import Dict

from portfolio.schemas.portfolio_schema import PortfolioDTO

logger = logging.getLogger(__name__)


class MarkdownGenerator:
    """
    Markdown Portfolio Generator.
    """

    def generate_markdown(self, portfolio: PortfolioDTO) -> str:
        """Generate comprehensive Markdown engineering portfolio."""
        md = f"""# Engineering Portfolio — {portfolio.project_name} (Project #{portfolio.project_id})

## 1. Executive Summary
{portfolio.executive_summary}

## 2. Project Vision & Objectives
**Vision**: {portfolio.project_vision}  
**Problem Statement**: {portfolio.problem_statement}

### Objectives
"""
        for obj in portfolio.objectives:
            md += f"- {obj}\n"

        md += f"""
## 3. Technology Stack
{", ".join(portfolio.technology_stack)}

## 4. Engineering Metrics
- **Lines of Code**: {portfolio.metrics.lines_of_code}
- **Number of Files**: {portfolio.metrics.number_of_files}
- **REST APIs**: {portfolio.metrics.number_of_apis}
- **Pydantic/SQLAlchemy Models**: {portfolio.metrics.number_of_models}
- **Database Tables & Relationships**: {portfolio.metrics.database_tables} tables, {portfolio.metrics.database_relationships} FKs
- **Validation Score**: {portfolio.metrics.validation_score:.1f}/100 ({portfolio.metrics.quality_grade})
- **Test Coverage**: {portfolio.metrics.test_coverage_pct:.1f}%

## 5. Architecture Overview
{portfolio.architecture.system_architecture}

## 6. AI Workflow & 13 Agent Collaboration
"""
        for wf in portfolio.agent_workflows:
            md += f"### {wf.agent_name.replace('_', ' ').title()}\n- **Responsibilities**: {wf.responsibilities}\n- **Runtime**: {wf.execution_time_ms}ms\n- **Status**: {wf.validation_status}\n\n"

        return md


markdown_generator = MarkdownGenerator()
