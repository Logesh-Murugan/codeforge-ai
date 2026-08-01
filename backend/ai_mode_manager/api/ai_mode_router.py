"""
AI Mode Router — Phase 5.6

FastAPI route handlers for the AI Mode Manager.

Endpoints:
    GET  /ai-mode/current     Get current active mode, provider, model, embedding
    GET  /ai-mode/providers   List registered AI providers & metadata
    GET  /ai-mode/models      List supported models for current mode
    GET  /ai-mode/embeddings  List supported embeddings for current mode
    GET  /ai-mode/status      Get active provider status and capabilities
    GET  /ai-mode/config      Retrieve AIConfiguration snapshot
    GET  /ai-mode/health      Run full health check on all providers
    POST /ai-mode/switch      Switch between local and cloud modes
    POST /ai-mode/config      Update configuration parameters
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from ai_mode_manager.embeddings.embedding_manager import EmbeddingManager
from ai_mode_manager.health.health_checker import ProviderHealthChecker
from ai_mode_manager.llms.model_manager import ModelManager
from ai_mode_manager.registry.provider_registry import provider_registry
from ai_mode_manager.schemas import (
    AIConfigResponse,
    EmbeddingInfoResponse,
    HealthStatus,
    ModelInfoResponse,
    ProviderInformation,
    SwitchModeRequest,
    UpdateConfigRequest,
    WorkingMode,
)
from ai_mode_manager.services.mode_manager import ModeManager, mode_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-mode", tags=["ai-mode-manager"])


def _mode_manager() -> ModeManager:
    return mode_manager


def _model_manager() -> ModelManager:
    return ModelManager()


def _embedding_manager() -> EmbeddingManager:
    return EmbeddingManager()


def _health_checker() -> ProviderHealthChecker:
    return ProviderHealthChecker()


@router.get(
    "/current",
    response_model=AIConfigResponse,
    summary="Get current active AI mode, provider, model, and embedding",
)
async def get_current_mode_info(
    _user=Depends(get_current_user),
    mgr: ModeManager = Depends(_mode_manager),
):
    """Return active mode configuration snapshot."""
    return mgr.get_configuration()


@router.get(
    "/providers",
    response_model=List[ProviderInformation],
    summary="List all registered AI providers & metadata",
)
async def list_providers(
    _user=Depends(get_current_user),
):
    """List details of all registered AI providers."""
    providers = provider_registry.list_providers()
    return [p.get_information() for p in providers]


@router.get(
    "/models",
    response_model=List[ModelInfoResponse],
    summary="List supported LLM models for current active mode",
)
async def list_models(
    mode: Optional[WorkingMode] = None,
    _user=Depends(get_current_user),
    model_mgr: ModelManager = Depends(_model_manager),
):
    """List available LLM models."""
    return model_mgr.list_available_models(mode)


@router.get(
    "/embeddings",
    response_model=List[EmbeddingInfoResponse],
    summary="List supported embedding models",
)
async def list_embeddings(
    mode: Optional[WorkingMode] = None,
    _user=Depends(get_current_user),
    emb_mgr: EmbeddingManager = Depends(_embedding_manager),
):
    """List available embedding models."""
    return emb_mgr.list_available_embeddings(mode)


@router.get(
    "/status",
    response_model=Dict[str, Any],
    summary="Get active provider status and health",
)
async def get_provider_status(
    _user=Depends(get_current_user),
    mgr: ModeManager = Depends(_mode_manager),
):
    """Return active provider status."""
    return await mgr.get_provider_status()


@router.get(
    "/config",
    response_model=AIConfigResponse,
    summary="Retrieve AIConfiguration snapshot",
)
async def get_config(
    _user=Depends(get_current_user),
    mgr: ModeManager = Depends(_mode_manager),
):
    """Retrieve full configuration snapshot."""
    return mgr.get_configuration()


@router.get(
    "/health",
    response_model=Dict[str, HealthStatus],
    summary="Run health check on all registered providers",
)
async def check_health(
    _user=Depends(get_current_user),
    checker: ProviderHealthChecker = Depends(_health_checker),
):
    """Run provider health monitoring suite."""
    return await checker.check_all_providers_health()


@router.post(
    "/switch",
    response_model=AIConfigResponse,
    summary="Switch between LOCAL and CLOUD mode",
)
async def switch_mode(
    req: SwitchModeRequest,
    _user=Depends(get_current_user),
    mgr: ModeManager = Depends(_mode_manager),
):
    """Switch active working mode."""
    return await mgr.switch_mode(
        mode=req.mode,
        provider=req.provider,
        model=req.model,
        embedding=req.embedding,
    )


@router.post(
    "/config",
    response_model=AIConfigResponse,
    summary="Update AI mode configuration",
)
async def update_config(
    req: UpdateConfigRequest,
    _user=Depends(get_current_user),
    mgr: ModeManager = Depends(_mode_manager),
):
    """Update mode configuration parameters."""
    return await mgr.update_configuration(req)
