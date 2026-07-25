"""
Backward-compatibility shim.

Old import path:  from memory.memory_service import MemoryService

New import path:  from memory.service import MemoryService
             or:  from memory import get_service

The MemoryService signature is unchanged — existing callers that pass
``embeddings_provider`` and ``store_manager`` keyword arguments will
still work, with parameter names mapped to the new constructor.
"""
from memory.service import MemoryService

__all__ = ["MemoryService"]
