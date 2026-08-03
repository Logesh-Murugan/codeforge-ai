import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, projects, memory
print("✓ auth/projects/memory imported")
from app.api.export import router as export_router
print("✓ export imported")
from app.api.validate import router as validate_router
print("✓ validate imported")
from app.api.testing import router as testing_router
print("✓ testing imported")
from memory.routers.persistent_memory import router as pmemory_router
print("✓ persistent memory imported")
from memory.routers.memory_engine import router as mengine_router
print("✓ memory engine imported")
from rag.routers.indexing import router as rag_index_router
print("✓ rag indexing imported")
from rag.routers.retrieval import router as rag_retrieval_router
print("✓ rag retrieval imported")
from approval.router import router as approval_router
print("✓ approval imported")
from collaboration.routers.collaboration import router as collaboration_router
print("✓ collaboration imported")
from context_engine.routers.context_router import router as context_router
print("✓ context imported")
from ai_mode_manager.api.ai_mode_router import router as ai_mode_router
print("✓ ai mode imported")
from monitoring.api.monitoring_router import router as monitoring_router
print("✓ monitoring imported")
from monitoring.api.monitoring_router import websocket_monitoring_endpoint
print("websocket_monitoring_endpoin imported")
from validation_pipeline.api.validation_router import router as validation_router
print("✓ validation imported")
from timeline.api.timeline_router import router as timeline_router
print("✓ timeline imported")
from portfolio.api.portfolio_router import router as portfolio_router
print("✓ portfolio imported")
from app.api.health import router as health_router
print("health_router impoerted")
from app.middleware.correlation_middleware import CorrelationMiddleware
print("correlationmiddleware imported")

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI Application Lifespan Handler."""
    from ai_mode_manager.registry.provider_registry import get_provider_registry
    registry = get_provider_registry()
    _ = registry.list_providers()
    yield


app = FastAPI(
    title="CodeForge AI Backend",
    description=(
        "Autonomous Software Engineering Platform v2.0.0. "
        "Complete 14-Phase Autonomous Engineering Suite featuring 13 AI Agents, Hybrid RAG, Memory Manager, Context Sharing, AI Mode Manager, Real-Time Monitoring, 12-Stage Validation Quality Gate, Project Timeline System, and Portfolio Output Package."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

import os

allowed_origin = os.getenv("ALLOWED_ORIGIN", "http://localhost:3000")
allow_origins = [allowed_origin]
if allowed_origin != "http://localhost:3000":
    allow_origins.extend(["http://localhost:3000", "http://127.0.0.1:3000"])

app.add_middleware(CorrelationMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(memory.router)
# Phase 4 routers
app.include_router(export_router)
app.include_router(validate_router)
app.include_router(testing_router)
# Phase 5.1 routers
app.include_router(pmemory_router)
app.include_router(mengine_router)
# Phase 5.2 — RAG Engine routers
app.include_router(rag_index_router)
app.include_router(rag_retrieval_router)
# Phase 5.3 — Human Approval Workflow router
app.include_router(approval_router)
# Phase 5.4 — Agent Collaboration Engine router
app.include_router(collaboration_router)
# Phase 5.5 — Context Sharing Engine router
app.include_router(context_router)
# Phase 5.6 — AI Mode Manager router
app.include_router(ai_mode_router)
# Phase 5.7 — Real-Time Monitoring System router
app.include_router(monitoring_router)
app.add_api_websocket_route("/ws/monitoring", websocket_monitoring_endpoint)
# Phase 5.8 — Validation Pipeline System router
app.include_router(validation_router)
# Phase 5.9 — Project Timeline System router
app.include_router(timeline_router)
# Phase 5.10 — Portfolio Output System router
app.include_router(portfolio_router)


@app.get("/")
async def root():
    return {"message": "CodeForge AI Backend"}


@app.get("/groq-health")
async def groq_health():
    import traceback
    from fastapi.responses import JSONResponse
    try:
        from agents.base_agent import BaseAgent
        # Run a minimal request to test the connection to Groq
        agent = BaseAgent(model="llama-3.1-8b-instant")
        res = agent.run("ping")
        if res:
            return {"status": "success"}
        else:
            return {"status": "failed", "exception": "Empty response received from Groq API"}
    except Exception as e:
        tb = traceback.format_exc()
        return JSONResponse(
            status_code=500,
            content={
                "status": "failed",
                "exception": f"{type(e).__name__}: {str(e)}",
                "traceback": tb
            }
        )
