"""
Communication Patterns Utility — Phase 5.4

Helpers for managing 9 agent communication patterns:
1. Sequential
2. Parallel
3. Cross-agent validation
4. Multi-agent consensus
5. Feedback propagation
6. Context propagation
7. Human approved collaboration
8. Collaboration retries
9. Failure recovery
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from collaboration.schemas.communication import CommunicationPattern


def resolve_communication_topology(pattern: CommunicationPattern, sender: str, receivers: List[str]) -> List[Dict[str, Any]]:
    """
    Build directed execution routes based on communication pattern.
    """
    routes: List[Dict[str, Any]] = []
    if pattern == CommunicationPattern.SEQUENTIAL:
        for receiver in receivers:
            routes.append({"sender": sender, "receiver": receiver, "mode": "sync"})
    elif pattern == CommunicationPattern.PARALLEL:
        for receiver in receivers:
            routes.append({"sender": sender, "receiver": receiver, "mode": "async"})
    elif pattern == CommunicationPattern.VALIDATION:
        for receiver in receivers:
            routes.append({"sender": sender, "receiver": receiver, "mode": "validation"})
    elif pattern == CommunicationPattern.FEEDBACK:
        for receiver in receivers:
            routes.append({"sender": sender, "receiver": receiver, "mode": "feedback"})
    else:  # CONSENSUS or default
        for receiver in receivers:
            routes.append({"sender": sender, "receiver": receiver, "mode": "consensus"})
    return routes
