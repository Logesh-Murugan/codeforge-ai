"""
Validator Registry — Phase 5.8

Thread-safe O(1) registry for managing concrete stage validators.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Type

logger = logging.getLogger(__name__)


class ValidatorRegistry:
    """
    Registry for managing 12 concrete stage validators.
    """

    def __init__(self) -> None:
        self._validators: Dict[str, Any] = {}

    def register(self, stage_name: str, validator_instance: Any) -> None:
        """Register validator instance under stage_name."""
        self._validators[stage_name] = validator_instance
        logger.debug(f"[ValidatorRegistry] Registered validator for stage: '{stage_name}'")

    def get_validator(self, stage_name: str) -> Any:
        """Retrieve validator instance by stage_name."""
        return self._validators.get(stage_name)

    def list_validators(self) -> List[Any]:
        """Return list of all registered validator instances in sequential order."""
        return list(self._validators.values())


validator_registry = ValidatorRegistry()
