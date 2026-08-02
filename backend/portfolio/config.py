"""
Portfolio Configuration — Phase 5.10
"""
from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings


class PortfolioSettings(BaseSettings):
    """
    Settings for Portfolio Output System.
    """

    PORTFOLIO_OUTPUT_DIR: str = Field(
        default="data/portfolios",
        description="Directory path where generated portfolio bundles are saved.",
    )

    ENABLE_MERMAID_DIAGRAMS: bool = Field(
        default=True,
        description="Enable automatic generation of Mermaid architecture & workflow diagrams.",
    )

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


portfolio_settings = PortfolioSettings()
