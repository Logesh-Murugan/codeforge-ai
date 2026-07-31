"""
SecurityMemoryEngine — Phase 5.1

Domain-specific memory engine for security analysis, vulnerability
tracking, remediation, and compliance records.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from memory.persistent_schemas import MemoryCategory, PersistentMemoryResponse
from memory.services.base_memory_service import BaseMemoryEngine

logger = logging.getLogger(__name__)


class SecurityMemoryEngine(BaseMemoryEngine):
    """Engine for security memory entries."""

    CATEGORY = MemoryCategory.SECURITY
    DOMAIN_FIELDS = [
        "severity", "vulnerability_type", "remediation",
        "scan_type", "affected_component", "cwe_id", "compliance",
    ]

    async def get_by_severity(
        self,
        project_id: int,
        severity: str,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryResponse]:
        """Retrieve entries filtered by severity level."""
        entries = await self.list_entries(project_id=project_id, session=session)
        return [
            e for e in entries
            if (e.metadata_json.get("severity") or "").lower() == severity.lower()
        ]

    async def get_by_vulnerability_type(
        self,
        project_id: int,
        vuln_type: str,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryResponse]:
        """Retrieve entries for a specific vulnerability type."""
        entries = await self.list_entries(project_id=project_id, session=session)
        return [
            e for e in entries
            if e.metadata_json.get("vulnerability_type") == vuln_type
        ]

    async def get_by_scan_type(
        self,
        project_id: int,
        scan_type: str,
        session: Optional[AsyncSession] = None,
    ) -> List[PersistentMemoryResponse]:
        """Retrieve entries filtered by scan type (sast/dast/dependency)."""
        entries = await self.list_entries(project_id=project_id, session=session)
        return [
            e for e in entries
            if e.metadata_json.get("scan_type") == scan_type
        ]

    async def get_security_dashboard(
        self,
        project_id: int,
        session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Build a security dashboard summary."""
        entries = await self.list_entries(
            project_id=project_id, limit=500, session=session,
        )
        by_severity: Dict[str, int] = {}
        by_scan_type: Dict[str, int] = {}
        by_vuln_type: Dict[str, int] = {}
        affected: List[str] = []
        compliance_set: set = set()

        for e in entries:
            meta = e.metadata_json
            sev = (meta.get("severity") or "unspecified").lower()
            by_severity[sev] = by_severity.get(sev, 0) + 1
            st = meta.get("scan_type")
            if st:
                by_scan_type[st] = by_scan_type.get(st, 0) + 1
            vt = meta.get("vulnerability_type")
            if vt:
                by_vuln_type[vt] = by_vuln_type.get(vt, 0) + 1
            ac = meta.get("affected_component")
            if ac:
                affected.append(ac)
            for c in meta.get("compliance", []) or []:
                compliance_set.add(c)

        return {
            "total": len(entries),
            "by_severity": by_severity,
            "by_scan_type": by_scan_type,
            "by_vulnerability_type": by_vuln_type,
            "affected_components": sorted(set(affected)),
            "compliance_frameworks": sorted(compliance_set),
        }
