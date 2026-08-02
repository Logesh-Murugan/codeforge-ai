<div align="center">

# ⚡ CodeForge AI `v2.0.0`
### Autonomous Enterprise Multi-Agent Software Engineering Platform

[![Version](https://img.shields.io/badge/Release-v2.0.0-blue?style=for-the-badge&logo=github)](docs/RELEASE_NOTES_v2.0.0.md)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14.2+-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-FF6B35?style=for-the-badge&logo=databricks&logoColor=white)](https://www.trychroma.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com)
[![Groq](https://img.shields.io/badge/Groq_Cloud-API-F55036?style=for-the-badge&logo=groq&logoColor=white)](https://groq.com)
[![Ollama](https://img.shields.io/badge/Ollama-Local_AI-000000?style=for-the-badge&logo=ollama&logoColor=white)](https://ollama.com)

<br />

**CodeForge AI is a state-of-the-art autonomous software engineering platform powered by a 13-Agent LangGraph workflow, hybrid local/cloud RAG, tiered memory management, real-time WebSocket monitoring, a 12-stage automated validation quality gate, project timeline telemetry, and an automated portfolio bundle exporter.**

<br />

[System Architecture](#-system-architecture) • [Key Capabilities](#-key-capabilities) • [13-Agent Orchestrator](#-13-agent-orchestration-pipeline) • [12-Stage Quality Gate](#-12-stage-validation-quality-gate) • [Quickstart](#-getting-started) • [Documentation](#-documentation)

---

</div>

<br />

## 🌟 Key Capabilities

CodeForge AI provides a complete end-to-end software development lifecycle (SDLC) automation solution:

- 🤖 **13-Agent LangGraph State Machine**: Specialized AI roles (PM, BA, PO, Architect, DB, API, Backend, Security, QA, Frontend, Reviewer, Docs, DevOps) collaborating deterministically.
- 🔄 **AI Mode Manager (LOCAL / CLOUD)**: Hot-swap between local Ollama models (`nomic-embed-text` / Llama 3) and cloud Groq inference engines with zero downtime.
- 🧠 **Tiered Memory & RAG Subsystem**: Working, Short-Term, Long-Term, and Ephemeral Context memory coupled with ChromaDB vector search and BM25 sparse keyword ranking.
- ⚡ **Real-Time WebSocket Telemetry**: EventBus event streaming (`/ws/monitoring`), live metrics engine, log viewer, and agent step tracking.
- 🛡️ **12-Stage Validation Quality Gate**: Automated structural, AST syntax, dependency, security (OWASP Top 10), Docker, database, API, and performance analysis with weighted A+ to F grading.
- ⏱️ **Project Timeline & Milestone Engine**: Persistent database event tracking, 9 automated milestone detectors, runtime statistics, and performance analytics.
- 📦 **Automated Portfolio & Diagram Exporter**: Generates 8 Mermaid architecture diagrams (Flowchart, ERD, Sequence, etc.), multi-format reports (MD, HTML, JSON, PDF Metadata), and a downloadable ZIP bundle.
- 🔒 **Enterprise Production Hardened**: Database connection pool recycling (`pool_recycle=3600`), correlation ID propagation (`X-Correlation-ID`), Zip Slip safety, prompt injection filters, and Kubernetes health probes (`/health`, `/health/liveness`, `/health/readiness`).

---

## 📐 System Architecture

```mermaid
flowchart TD
    subgraph Frontend["Frontend Layer (Next.js 14 / Tailwind CSS)"]
        UI["Dashboard & Studio Pages"]
        MON_UI["Real-Time Monitoring Dashboard"]
        VAL_UI["Validation Quality Gate Dashboard"]
        TIM_UI["Project Timeline & Milestones"]
        PORT_UI["Portfolio & Diagram Center"]
    end

    subgraph Backend["Backend API Layer (FastAPI / Python 3.11)"]
        API["FastAPI Router Engine"]
        AUTH["JWT Auth & RBAC Security"]
        CORR["Correlation Middleware"]
        HLTH["Health & Diagnostic Probes"]
    end

    subgraph CoreEngine["Autonomous Core Subsystems"]
        ORCH["13-Agent LangGraph Orchestrator"]
        RAG["Hybrid RAG & ChromaDB Engine"]
        MEM["Tiered Memory Manager"]
        MODE["AI Mode Manager (LOCAL / CLOUD)"]
        BUS["EventBus & Telemetry Collector"]
        VAL["12-Stage Validation Quality Gate"]
        TIM["Timeline Repository & Engine"]
        PORT["Portfolio & Mermaid Diagram Service"]
    end

    UI --> API
    MON_UI --> BUS
    VAL_UI --> VAL
    TIM_UI --> TIM
    PORT_UI --> PORT

    API --> AUTH
    API --> CORR
    API --> HLTH
    API --> ORCH

    ORCH --> RAG
    ORCH --> MEM
    ORCH --> MODE
    ORCH --> BUS
    ORCH --> VAL
    VAL --> TIM
    TIM --> PORT
```

---

## 👥 13-Agent Orchestration Pipeline

| # | Agent Role | Core Responsibility | Default Artifact Output |
|---|------------|---------------------|--------------------------|
| 1 | **Project Manager** | Master project plan, task decomposition, milestone scoping | `tasks.json` |
| 2 | **Business Analyst** | User stories, domain entity mapping, acceptance criteria | `requirements.md` |
| 3 | **Product Owner** | Feature prioritization & Product Requirement Document | `prd.md` |
| 4 | **Solution Architect** | System architecture, layer boundaries, design patterns | `architecture.md` |
| 5 | **Database Engineer** | Entity Relationship specs, SQLAlchemy models, migration scripts | `schema.sql`, `models.py` |
| 6 | **API Designer** | OpenAPI 3.1 specification, request/response DTO contracts | `openapi.json` |
| 7 | **Backend Developer** | Production FastAPI application, routers, services, repositories | `main.py`, `services.py` |
| 8 | **Security Engineer** | OWASP Top 10 security audit, JWT hardening, secret scanning | `security.py` |
| 9 | **QA Engineer** | Automated unit, integration, and API test suites | `test_main.py` |
| 10 | **Frontend Developer** | Next.js App Router pages, React Server Components, Tailwind UI | `page.tsx`, `components/` |
| 11 | **Code Reviewer** | Code quality inspection, anti-pattern detection, refactoring | `review_notes.md` |
| 12 | **Documentation Writer** | Comprehensive README, installation & deployment guides | `README.md` |
| 13 | **DevOps Engineer** | Dockerfile, docker-compose, Nginx, deployment pipelines | `Dockerfile`, `docker-compose.yml` |

---

## 🛡️ 12-Stage Validation Quality Gate

Every generated codebase passes through a mandatory 12-stage validation pipeline prior to export:

```
Codebase → [1. Structure] → [2. Syntax (AST)] → [3. Dependencies] → [4. Architecture]
         → [5. Database]  → [6. API Routes]    → [7. Security]     → [8. Documentation]
         → [9. Docker]     → [10. Testing]     → [11. Performance] → [12. Code Quality]
         → Weighted Quality Score (0-100) & Grade (A+ to F) → Export Approval
```

| Grade | Score Threshold | Export Status |
|-------|-----------------|---------------|
| **A+** | 95.0 – 100.0 | **Production Ready** ✅ |
| **A** | 90.0 – 94.9 | **Excellent** ✅ |
| **B** | 80.0 – 89.9 | **Good** ✅ |
| **C** | 70.0 – 79.9 | **Needs Improvement** ⚠️ |
| **F** | Below 70.0 | **Validation Failed** ❌ |

---

## 🚀 Getting Started

### Prerequisites
- **Python**: 3.11+
- **Node.js**: 18+ & npm
- **Database**: PostgreSQL (or SQLite for local dev)
- **AI Mode**: [Groq API Key](https://console.groq.com) (CLOUD) or [Ollama](https://ollama.com) (LOCAL)

---

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate   # On Windows
# source venv/bin/activate  # On Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
```

Edit `backend/.env`:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/codeforge
JWT_SECRET_KEY=your-secure-jwt-secret-key
GROQ_API_KEY=gsk_your_groq_api_key_here

# Provider Mode (GROQ or OLLAMA)
AI_PROVIDER_MODE=GROQ
OLLAMA_BASE_URL=http://localhost:11434
```

Start the FastAPI production server:
```bash
python -m uvicorn app.main:app --reload --port 8000
```

---

### 2. Frontend Setup

```bash
cd frontend

# Install packages
npm install

# Start Next.js dev server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

### 3. Docker Compose (Full Stack)

```bash
# Start backend, database, and frontend containers
docker-compose up --build
```

---

## 🧪 Release Verification & Testing

Run the master v2.0.0 release verification test suite:

```bash
cd backend
python scratch/verify_release_v2_suite.py
```

Check health probe endpoints:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/liveness
curl http://localhost:8000/health/readiness
curl http://localhost:8000/health/diagnostics
```

---

## 📚 Documentation & Guides

Comprehensive technical documentation is available in the [`docs/`](docs/) directory:

- 🏛️ [**System Architecture Guide**](docs/ARCHITECTURE.md): Full 14-phase subsystem blueprint.
- 💻 [**Developer & Contributor Guide**](docs/DEVELOPER_GUIDE.md): Setup, workflow, and testing.
- 🐳 [**Production Deployment Guide**](docs/DEPLOYMENT_GUIDE.md): Docker & Kubernetes configuration.
- 🔌 [**API Reference Guide**](docs/API_GUIDE.md): Complete OpenAPI REST & WebSocket endpoints map.
- 🚀 [**v2.0.0 Release Notes**](docs/RELEASE_NOTES_v2.0.0.md): Official release notes & production checklists.
- 📝 [**CHANGELOG**](docs/CHANGELOG.md): Version history from Phase 1 through Phase 5.11.

---

## 📄 License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for details.
