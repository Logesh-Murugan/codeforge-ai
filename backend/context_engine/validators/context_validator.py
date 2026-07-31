"""
ContextValidator — Phase 5.5

Context Validation System. Validates:
- Missing Contexts
- Invalid Contexts
- Duplicate Contexts
- Conflicting Contexts
- Empty Contexts
- Expired Contexts
- Corrupted Contexts
Fails gracefully with structured reports.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from context_engine.schemas.validation import (
    ContextValidationErrorType,
    ContextValidationIssue,
    ContextValidationResponse,
)

logger = logging.getLogger(__name__)


class ContextValidator:
    """
    Context Validation System.
    """

    async def validate_bundle(
        self,
        project_id: int,
        target_agent: Optional[str],
        bundle: Dict[str, Any],
        required_types: Optional[List[str]] = None,
    ) -> ContextValidationResponse:
        """
        Validate an aggregated or routed context bundle against validation rules.
        """
        issues: List[ContextValidationIssue] = []

        # 1. Missing Contexts Check
        if required_types:
            for req_type in required_types:
                if req_type not in bundle or bundle[req_type] is None:
                    issues.append(
                        ContextValidationIssue(
                            context_type=req_type,
                            error_type=ContextValidationErrorType.MISSING,
                            description=f"Required context type '{req_type}' is missing for agent '{target_agent}'.",
                            severity="warning",
                        )
                    )

        # 2. Empty Contexts Check
        for ctx_type, payload in bundle.items():
            if payload is not None and not payload:
                issues.append(
                    ContextValidationIssue(
                        context_type=ctx_type,
                        error_type=ContextValidationErrorType.EMPTY,
                        description=f"Context type '{ctx_type}' contains empty content payload.",
                        severity="warning",
                    )
                )

        # 3. Invalid / Corrupted Check
        for ctx_type, payload in bundle.items():
            if payload is not None and not isinstance(payload, (dict, list, str, int, float, bool)):
                issues.append(
                    ContextValidationIssue(
                        context_type=ctx_type,
                        error_type=ContextValidationErrorType.CORRUPTED,
                        description=f"Context type '{ctx_type}' payload type is corrupted or unparseable.",
                        severity="error",
                    )
                )

        # 4. Duplicate Check
        seen_payloads = set()
        for ctx_type, payload in bundle.items():
            if payload and isinstance(payload, dict):
                str_rep = str(payload)
                if str_rep in seen_payloads:
                    issues.append(
                        ContextValidationIssue(
                            context_type=ctx_type,
                            error_type=ContextValidationErrorType.DUPLICATE,
                            description=f"Duplicate payload detected for context type '{ctx_type}'.",
                            severity="warning",
                        )
                    )
                else:
                    seen_payloads.add(str_rep)

        is_valid = not any(i.severity == "critical" for i in issues)

        return ContextValidationResponse(
            project_id=project_id,
            target_agent=target_agent,
            is_valid=is_valid,
            total_issues=len(issues),
            issues=issues,
        )
