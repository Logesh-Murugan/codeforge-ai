"""
Base Validator ABC — Phase 5.8
"""
from __future__ import annotations

import abc
import time
from typing import Any, Dict, List
from validation_pipeline.severity import IssueSeverity
from validation_pipeline.validator_result import StageResult, ValidationIssue


class BaseValidator(abc.ABC):
    """
    Abstract Base Class for all 12 concrete stage validators.
    """

    def __init__(self, stage_name: str) -> None:
        self.stage_name = stage_name

    @abc.abstractmethod
    async def validate(self, project_path: str, context: Dict[str, Any]) -> StageResult:
        """
        Execute stage validation against project_path codebase.
        """
        pass
