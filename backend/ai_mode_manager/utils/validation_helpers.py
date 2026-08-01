"""
Validation Helpers — Phase 5.6

Helper utilities for sanitizing inputs, validating models, and building recommendations.
"""
from __future__ import annotations

from typing import Dict, List, Optional


def sanitize_provider_name(name: str) -> str:
    """Sanitize provider name strings."""
    return name.strip().lower()


def validate_mode_string(mode_str: str) -> bool:
    """Check if string is a valid working mode."""
    return mode_str.lower() in ("local", "cloud")
