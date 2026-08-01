"""
Request & Response Schemas — Phase 5.6

Pydantic models for REST API requests and responses.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from ai_mode_manager.schemas.mode_state import HealthStatus, WorkingMode


class SwitchModeRequest(BaseModel):
    mode: WorkingMode = Field(..., description="Target mode (local or cloud).")
    provider: Optional[str] = Field(None, description="Optional target provider name.")
    model: Optional[str] = Field(None, description="Optional target model name.")
    embedding: Optional[str] = Field(None, description="Optional target embedding model.")


class UpdateConfigRequest(BaseModel):
    mode: Optional[WorkingMode] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    embedding: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class AIConfigResponse(BaseModel):
    mode: WorkingMode
    active_provider: str
    active_model: str
    active_embedding: str
    health_status: HealthStatus
    validation_status: str = "valid"
    available_modes: List[str] = Field(default_factory=lambda: ["local", "cloud"])


class ModelInfoResponse(BaseModel):
    name: str
    provider: str
    is_recommended: bool = False
    context_length: int = 128000


class EmbeddingInfoResponse(BaseModel):
    name: str
    provider: str
    dimension: int = 384
