from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, projects, memory
from app.api.export import router as export_router
from app.api.validate import router as validate_router
from app.api.testing import router as testing_router
from memory.routers.persistent_memory import router as pmemory_router
from memory.routers.memory_engine import router as mengine_router
from rag.routers.indexing import router as rag_index_router
from rag.routers.retrieval import router as rag_retrieval_router
from approval.router import router as approval_router
from collaboration.routers.collaboration import router as collaboration_router
from context_engine.routers.context_router import router as context_router
from ai_mode_manager.api.ai_mode_router import router as ai_mode_router
from monitoring.api.monitoring_router import router as monitoring_router
from monitoring.api.monitoring_router import websocket_monitoring_endpoint
from validation_pipeline.api.validation_router import router as validation_router

app = FastAPI(
    title="CodeForge AI Backend",
    description=(
        "Autonomous Software Engineering Platform. "
        "Phase 1–5: Project generation, validation, testing, export, memory, RAG, approval, collaboration, context sharing, AI mode manager, real-time monitoring system, and validation pipeline quality gate."
    ),
    version="5.8.0",
)

import os

allowed_origin = os.getenv("ALLOWED_ORIGIN", "http://localhost:3000")
allow_origins = [allowed_origin]
if allowed_origin != "http://localhost:3000":
    allow_origins.extend(["http://localhost:3000", "http://127.0.0.1:3000"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
