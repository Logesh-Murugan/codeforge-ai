"""
memory.context — Phase 3.5 Agent Context Sharing
=================================================

Four focused components that together give every agent in the pipeline
access to the right memory at the right time.

Components
----------
ContextInjector
    Builds rich, role-aware prompt blocks from project memory.
    Each agent role has a pre-configured set of collections it reads
    and a default relevance query template.

CrossAgentMemory
    Shared memory bus that lets any agent read artifacts produced by
    any other agent in the same project.

LongTermMemory
    Decay-weighted semantic retrieval. Recent, high-importance records
    surface ahead of old, low-confidence ones.

ConversationMemory
    Persistent multi-turn conversation buffer scoped per project (and
    optionally per session).  Handles role normalisation, windowing,
    and serialisation.
"""
from memory.context.injector import ContextInjector, AgentRole, AGENT_ROLES
from memory.context.cross_agent import CrossAgentMemory
from memory.context.long_term import LongTermMemory
from memory.context.conversation import ConversationMemory

__all__ = [
    "ContextInjector",
    "AgentRole",
    "AGENT_ROLES",
    "CrossAgentMemory",
    "LongTermMemory",
    "ConversationMemory",
]
