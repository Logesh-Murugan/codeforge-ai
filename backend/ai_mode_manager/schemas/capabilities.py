"""
Provider Capabilities & Information Schemas — Phase 5.6
"""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field

from ai_mode_manager.schemas.mode_state import HealthStatus, ProviderType, WorkingMode


class ProviderCapabilities(BaseModel):
    supports_llm: bool = Field(default=True)
    supports_embedding: bool = Field(default=True)
    supports_streaming: bool = Field(default=True)
    supports_vision: bool = Field(default=False)
    supports_function_calling: bool = Field(default=True)
    max_context_length: int = Field(default=128000)


class ProviderInformation(BaseModel):
    provider_id: str
    name: str
    provider_type: ProviderType
    mode: WorkingMode
    health_status: HealthStatus = Field(default=HealthStatus.UNKNOWN)
    supported_models: List[str] = Field(default_factory=list)
    supported_embeddings: List[str] = Field(default_factory=list)
    capabilities: ProviderCapabilities = Field(default_factory=ProviderCapabilities)
    is_available: bool = Field(default=True)
