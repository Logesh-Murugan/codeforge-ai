"""
Memory helper utilities — Phase 5.1

Shared functions used by all domain-specific memory engines.  These are
pure helpers with no side effects — safe to call from any context.
"""
from __future__ import annotations

import html
import re
from typing import Any, Dict, List, Optional

from memory.persistent_schemas import MemoryCategory


# ── Category mapping ────────────────────────────────────────────────────────

_DOMAIN_TO_CATEGORY: Dict[str, MemoryCategory] = {
    "project": MemoryCategory.PROJECT,
    "agent": MemoryCategory.AGENT,
    "requirement": MemoryCategory.REQUIREMENT,
    "architecture": MemoryCategory.ARCHITECTURE,
    "database": MemoryCategory.DATABASE,
    "api": MemoryCategory.API,
    "backend": MemoryCategory.BACKEND,
    "frontend": MemoryCategory.FRONTEND,
    "security": MemoryCategory.SECURITY,
    "testing": MemoryCategory.TESTING,
    "deployment": MemoryCategory.DEPLOYMENT,
    "documentation": MemoryCategory.DOCUMENTATION,
}

VALID_DOMAINS: List[str] = list(_DOMAIN_TO_CATEGORY.keys())


def validate_domain(domain: str) -> MemoryCategory:
    """
    Map a domain path-parameter string to the corresponding
    ``MemoryCategory`` enum value.

    Raises:
        ValueError: If the domain is not recognised.
    """
    cat = _DOMAIN_TO_CATEGORY.get(domain.lower())
    if cat is None:
        raise ValueError(
            f"Unknown memory domain '{domain}'. "
            f"Valid domains: {', '.join(VALID_DOMAINS)}"
        )
    return cat


# ── Metadata helpers ────────────────────────────────────────────────────────

def merge_metadata(
    existing: Dict[str, Any],
    updates: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Deep-merge *updates* into *existing*, returning a new dict.

    - ``None`` values in *updates* remove the key from *existing*.
    - Nested dicts are merged recursively.
    - All other values are overwritten.
    """
    if updates is None:
        return dict(existing)

    merged = dict(existing)
    for key, value in updates.items():
        if value is None:
            merged.pop(key, None)
        elif isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_metadata(merged[key], value)
        else:
            merged[key] = value
    return merged


def inject_domain_fields(
    metadata_json: Dict[str, Any],
    domain_fields: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Inject domain-specific fields into the metadata_json dict.

    Only non-None values are written, preserving existing keys.
    """
    result = dict(metadata_json)
    for key, value in domain_fields.items():
        if value is not None:
            result[key] = value
    return result


def extract_domain_fields(
    metadata_json: Dict[str, Any],
    field_names: List[str],
) -> Dict[str, Any]:
    """
    Extract domain-specific fields from metadata_json.

    Returns a dict containing only the keys listed in *field_names*
    that are present in the metadata.
    """
    return {k: metadata_json[k] for k in field_names if k in metadata_json}


# ── Content sanitisation ────────────────────────────────────────────────────

_STRIP_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def sanitize_content(content: str) -> str:
    """
    Sanitise memory content before storage.

    - Strip control characters (except newline, carriage return, tab).
    - Escape HTML entities to prevent injection.
    - Trim leading / trailing whitespace.
    """
    cleaned = _STRIP_PATTERN.sub("", content)
    cleaned = html.escape(cleaned)
    return cleaned.strip()


# ── Search metadata ─────────────────────────────────────────────────────────

def build_search_metadata(
    project_id: int,
    category: Optional[str] = None,
    agent_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build a ChromaDB ``where`` filter dict from common query parameters.
    """
    where: Dict[str, Any] = {"project_id": project_id}
    if category:
        where["category"] = category
    if agent_name:
        where["agent_name"] = agent_name
    return where


# ── Response formatting ─────────────────────────────────────────────────────

def format_memory_response(
    entry_data: Dict[str, Any],
    domain_field_names: List[str],
) -> Dict[str, Any]:
    """
    Augment a raw persistent memory response dict with extracted
    domain-specific fields from its ``metadata_json``.
    """
    meta = entry_data.get("metadata_json", {})
    for field_name in domain_field_names:
        if field_name in meta:
            entry_data[field_name] = meta[field_name]
    return entry_data
