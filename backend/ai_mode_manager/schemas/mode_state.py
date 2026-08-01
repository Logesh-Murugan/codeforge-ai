"""
Mode State & Health Schemas — Phase 5.6

Enums and Pydantic models for ModeState, HealthStatus, and ProviderMetadata.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WorkingMode(str, Enum):
    LOCAL = "local"
    CLOUD = "cloud"


class HealthStatus(str, Enum):
    CONNECTED = "Connected"
    DISCONNECTED = "Disconnected"
    UNAVAILABLE = "Unavailable"
    UNKNOWN = "Unknown"


class ProviderType(str, Enum):
    OLLAMA = "ollama"
    GROQ = "groq"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    AZURE = "azure_openai"
    BEDROCK = "aws_bedrock"
    TOGETHER = "together"
    OPENROUTER = "openrouter"


class ProviderMetadata(BaseModel):
    name: str = Field(..., description="Display name of the provider.")
    provider_type: ProviderType = Field(..., description="Provider type identifier.")
    mode: WorkingMode = Field(..., description="Mode (local or cloud).")
    is_active: bool = Field(default=False)
    description: str = Field(default="")
    version: str = Field(default="1.0.0")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ModeState(BaseModel):
    mode: WorkingMode = Field(default=WorkingMode.CLOUD)
    active_provider: str = Field(default="groq")
    active_model: str = Field(default="llama-3.1-8b")
    active_embedding: str = Field(default="all-MiniLM-L6-v2")
    health_status: HealthStatus = Field(default=HealthStatus.CONNECTED)
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_validated: bool = Field(default=True)
