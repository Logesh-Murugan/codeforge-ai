# CodeForge AI — System Architecture Guide (v2.0.0)

## Overview
CodeForge AI is an autonomous, production-ready software engineering platform built with a 13-agent LangGraph workflow, hybrid local/cloud RAG architecture, tiered memory subsystem, real-time monitoring engine, 12-stage validation quality gate, persistent project timeline, and automated portfolio bundle exporter.

---

## Subsystems Map (Phases 1 — 5.11)

### 1. Multi-Agent Orchestrator (`backend/orchestrator/` & `backend/agents/`)
- 13 Specialized AI Agents: Project Manager, Business Analyst, Product Owner, Solution Architect, Database Engineer, API Designer, Backend Developer, Security Engineer, QA Engineer, Frontend Developer, Code Reviewer, Documentation Writer, DevOps Engineer.

### 2. Hybrid RAG Engine (`backend/rag/`)
- Local/Cloud RAG architecture with ChromaDB vector search and BM25 sparse keyword retrieval.

### 3. Memory Subsystem (`backend/memory/`)
- Tiered Memory Architecture: Working Memory, Short-Term Memory, Long-Term Memory, and Ephemeral Context engine.

### 4. Context Sharing Engine (`backend/context_engine/`)
- Inter-agent context validation, state graph serialization, and cross-agent context sharing.

### 5. AI Mode Manager (`backend/ai_mode_manager/`)
- Provider-independent AI abstraction supporting Ollama (LOCAL) and Groq (CLOUD) execution modes with zero downtime runtime switching.

### 6. Real-Time Monitoring System (`backend/monitoring/`)
- Real-time WebSocket telemetry stream (`/ws/monitoring`), EventBus, agent execution step collector, metrics engine, and live monitoring dashboard.

### 7. Validation Pipeline System (`backend/validation_pipeline/`)
- Mandatory 12-stage sequential quality gate: Structure, AST Syntax, Dependency, Architecture, Database, API, Security (OWASP Top 10), Documentation, Docker, Testing, Performance, and Code Quality. Calculates weighted quality grade (A+ to F).

### 8. Project Timeline System (`backend/timeline/`)
- Central history & telemetry engine. Stores every lifecycle event in SQLAlchemy 2.0 DB, detects 9 automated milestones, and computes performance analytics.

### 9. Portfolio Output System (`backend/portfolio/`)
- Automatically transforms generated project codebases into an engineering portfolio package complete with 8 Mermaid diagrams (Flowchart, Sequence, ERD, Component, Class, State, Deployment, Architecture), multi-format reports (MD, HTML, JSON, PDF Metadata), and a downloadable ZIP bundle.

### 10. Production Hardening & Health (`backend/app/core/` & `backend/app/api/health.py`)
- Connection pool recycling (`pool_recycle=3600`), correlation ID propagation (`X-Correlation-ID`), Zip Slip protection, prompt injection filter, and production health probes (`/health`, `/health/liveness`, `/health/readiness`, `/health/diagnostics`).
