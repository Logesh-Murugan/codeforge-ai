# 🛠️ CodeForge AI

<div align="center">

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-FF6B35?style=for-the-badge&logo=databricks&logoColor=white)](https://www.trychroma.com)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com)
[![Groq](https://img.shields.io/badge/Groq_Cloud-F55036?style=for-the-badge&logo=groq&logoColor=white)](https://groq.com)
[![Ollama](https://img.shields.io/badge/Ollama-000000?style=for-the-badge&logo=ollama&logoColor=white)](https://ollama.com)

**An enterprise-grade, multi-agent AI software developer system that designs, builds, reviews, documents, and remembers — generating fully-functional, secure backend + frontend applications from simple natural language descriptions.**

[Architecture](#-system-architecture--flow) • [Memory System](#-memory-system-phases-31--33) • [Agents](#-agent-pipeline) • [Setup](#-getting-started) • [Testing](#-testing) • [Deployment](DEPLOYMENT.md)

</div>

---

## 📐 System Architecture & Flow

CodeForge AI runs a deterministic **13-Agent LangGraph state machine**. Each agent operates as a specialised role within a simulated software development team. Every agent output is automatically embedded and stored in a persistent vector memory, enabling downstream agents to retrieve relevant context from previous work.

```mermaid
flowchart TD
    A[User Prompt] --> PM[Project Manager]
    PM --> BA[Business Analyst]
    BA --> PO[Product Owner]
    PO --> SA[Solution Architect]
    SA --> DB[Database Engineer]
    SA --> AD[API Designer]
    DB --> BD[Backend Developer]
    AD --> BD
    BD --> SE[Security Engineer]
    SE --> QA[QA Engineer]
    QA --> FE[Frontend Developer]
    FE --> CR[Code Reviewer]
    CR --> DW[Documentation Writer]
    DW --> DO[DevOps Engineer]
    DO -->|Generated Files + Memory| VDB[(ChromaDB Vector Store)]
    VDB --> ZIP[Download ZIP Archive]
```

---

## 👥 Agent Pipeline

| # | Agent | Model | Responsibility |
|---|-------|-------|----------------|
| 1 | **Project Manager** | Llama 3.3-70b | Master project plan, milestones, risk assessment |
| 2 | **Business Analyst** | Llama 3.1-8b | User stories, entity mapping, requirements |
| 3 | **Product Owner** | Llama 3.1-8b | Sprint backlog, feature prioritisation, acceptance criteria |
| 4 | **Solution Architect** | Llama 3.3-70b | DB schema, API routes, file structure |
| 5 | **Database Engineer** | Llama 3.3-70b | ER diagrams, indexes, SQLAlchemy models, migrations |
| 6 | **API Designer** | Llama 3.3-70b | OpenAPI 3.1 spec, request/response models, auth flows |
| 7 | **Backend Developer** | Llama 3.3-70b | FastAPI codebase, routes, services, middleware |
| 8 | **Security Engineer** | Llama 3.3-70b | OWASP audit, JWT hardening, secrets detection |
| 9 | **QA Engineer** | Llama 3.3-70b | Test plan, unit + integration + API test code |
| 10 | **Frontend Developer** | Llama 3.3-70b | Next.js pages, components, Tailwind UI |
| 11 | **Code Reviewer** | Llama 3.3-70b | Security audit, auto-fix, style enforcement |
| 12 | **Documentation Writer** | Llama 3.1-8b | README, API docs, deployment guides |
| 13 | **DevOps Engineer** | Llama 3.3-70b | Dockerfile, docker-compose, GitHub Actions, nginx |

---

## 🧠 Memory System (Phases 3.1 – 3.3)

CodeForge AI includes a fully modular, open-source persistent memory subsystem built on **ChromaDB** and a provider-agnostic embedding architecture. No OpenAI dependency. No vendor lock-in.

### Architecture

```
backend/memory/
├── interfaces/          ← ABCs: EmbeddingProviderInterface, VectorStoreInterface, MemoryProviderInterface
├── embeddings/          ← LocalEmbeddings · OllamaEmbeddings · HuggingFaceEmbeddings · resolver
├── vectorstores/        ← ChromaVectorStore (12 persistent collections)
├── rag/                 ← RAG Pipeline: chunker · storage · retrieval · pipeline
├── utils/               ← cosine_similarity · chunking · LRU cache
├── schemas.py           ← Pydantic contracts
├── config.py            ← MemorySettings (env-var driven)
├── service.py           ← MemoryService façade
└── manager.py           ← MemoryManager (provider registry + lifecycle)
```

### Embedding Providers

| Provider | Mode | Model | Deps | Health Check |
|----------|------|-------|------|-------------|
| `LocalEmbeddings` | Any | Hash-projection (1536-dim) | None | Always ✓ |
| `OllamaEmbeddings` | Local | `nomic-embed-text` (768-dim) | httpx | GET /api/tags |
| `HuggingFaceEmbeddings` | Cloud | `all-MiniLM-L6-v2` (384-dim) | httpx | Ping embed |

Provider resolution follows a configurable fallback chain: `EMBEDDING_PROVIDER` → `EMBEDDING_FALLBACK_CHAIN` → `LocalEmbeddings` (guaranteed final fallback).

### RAG Pipeline

The `memory/rag/` package provides a production-grade Retrieval-Augmented Generation pipeline:

**Ingest path:**
```
text → ChunkingEngine → StorageEngine → ChromaDB
                ↓             ↓
         4 strategies    content-hash dedup
         word-boundary   batch upsert (configurable)
         configurable    version mirror → project_history
```

**Retrieval path:**
```
query → embed → ANN search → exact cosine re-rank → MetadataFilter → MMR → results
```

**Chunking strategies:**

| Strategy | How it splits |
|----------|---------------|
| `CHARACTER` | Fixed-size windows with optional word-boundary snapping |
| `SENTENCE` | Split on `.!?` boundaries, window if still large |
| `PARAGRAPH` | Split on blank lines, window large paragraphs |
| `RECURSIVE` | Paragraph → sentence → character cascade (best quality) |

**Memory collections (12):**

`requirements` · `architecture` · `database_design` · `api_contracts` · `backend_code` · `frontend_code` · `security_reports` · `qa_reports` · `documentation` · `devops` · `conversation` · `project_history`

### Memory Configuration

```env
# Deployment mode: local (Ollama) or cloud (HuggingFace)
MEMORY_MODE=local
EMBEDDING_PROVIDER=local           # local | ollama | huggingface
EMBEDDING_FALLBACK_CHAIN=ollama,huggingface,local

# LOCAL — Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBED_MODEL=nomic-embed-text

# CLOUD — HuggingFace Inference API
HF_API_TOKEN=hf_...
HF_EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2

# RAG tuning
RAG_CHUNK_SIZE=800
RAG_CHUNK_OVERLAP=100
RAG_DEFAULT_LIMIT=5
RAG_DEFAULT_THRESHOLD=0.0

# Cache
EMBEDDING_CACHE_ENABLED=true
EMBEDDING_CACHE_MAX_SIZE=512
```

---

## 🌟 Key Technical Achievements

> **All achievements are verified by the automated test suite (129 passing tests).**

- **🧠 Persistent Vector Memory**: Every agent artifact is chunked, embedded, and stored in ChromaDB. Downstream agents retrieve semantically relevant context from prior agent outputs before generating their own.
- **🔌 Provider Abstraction**: Three embedding providers (Local hash-projection, Ollama, HuggingFace) behind clean ABCs. Switch between local and cloud mode with a single env-var change. No OpenAI dependency.
- **📄 4-Strategy Chunker**: Character, sentence, paragraph, and recursive splitting with overlap, word-boundary snapping, min-size filtering, and content-hash deduplication.
- **🔍 Semantic Retrieval with MMR**: ANN search + exact cosine re-ranking + optional Maximal Marginal Relevance for diverse context windows. Supports AND/OR compound metadata filtering.
- **💾 Serverless-Ready Storage**: Projects are saved as dynamic JSON objects in PostgreSQL — no temp files, no disk writes.
- **⚡ In-Memory ZIP Compiling**: `zipfile` + `io.BytesIO` packages codebases on-the-fly. No cleanup required.
- **🌐 Render Connection Solver**: Custom `httpx.HTTPTransport(local_address="0.0.0.0")` bypasses dual-stack IPv6 timeouts on Render.
- **🛡️ Robust JSON Extraction**: Markdown fence splitting, `{}` boundary isolation, `strict=False` parsing for agent outputs.

---

## 🛠️ Technology Stack

| Layer | Technology | Details |
|:------|:-----------|:--------|
| **Backend Core** | FastAPI | Async REST API, Python 3.10+ |
| **Orchestration** | LangGraph | 13-node deterministic state machine |
| **Database** | PostgreSQL + Alembic | Neon serverless DB, schema migrations |
| **Vector Store** | ChromaDB | Persistent local embedding store |
| **Embeddings** | Ollama / HuggingFace / Local | Provider-switchable via env-var |
| **AI Interface** | OpenAI SDK v1.54.4 | Groq API compatibility layer |
| **Frontend** | Next.js 14/15 | Glassmorphic dashboard, Tailwind CSS |
| **Containerisation** | Docker + Compose | One-command deployment |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL (or [Neon](https://neon.tech) serverless)
- *(Optional for local embeddings)* [Ollama](https://ollama.com) with `nomic-embed-text` pulled

### 1. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Copy and edit environment config
cp .env.example .env
```

Edit `backend/.env`:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/codeforge
JWT_SECRET_KEY=your-secure-secret-key
GROQ_API_KEY=gsk_your_groq_key_here

# Memory system (choose a mode)
MEMORY_MODE=local
EMBEDDING_PROVIDER=local          # Use 'ollama' if Ollama is running
```

Run migrations and start:

```bash
alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### 3. (Optional) Start Ollama for Local Embeddings

```bash
# Pull the embedding model
ollama pull nomic-embed-text

# Ollama runs on http://localhost:11434 by default
# Set EMBEDDING_PROVIDER=ollama in your .env
```

---

### 🐳 Docker Compose (Full Stack)

```bash
# Create root .env with your Groq key
echo "GROQ_API_KEY=gsk_your_key_here" > .env

# Build and start
docker-compose up --build

# Start frontend separately
cd frontend && npm run dev
```

---

## 🧪 Testing

### Run all memory + RAG tests

```bash
cd backend
python -m pytest tests/test_memory.py tests/test_memory_architecture.py tests/test_rag_pipeline.py -v
```

**129 tests, 0 failures** across:

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_memory.py` | 2 | CRUD lifecycle regression |
| `test_memory_architecture.py` | 77 | Providers, interfaces, schemas, config, manager |
| `test_rag_pipeline.py` | 52 | Chunker (4 strategies), storage, retrieval, pipeline, MMR, MetadataFilter |

### Run the agent pipeline smoke test

```bash
cd backend
python smoke_test.py
```

### Health check

```bash
curl http://127.0.0.1:8000/groq-health
# → {"status": "success"}
```

---

## 📁 Project Structure

```
codeforge-ai/
├── backend/
│   ├── agents/              ← 13 specialised LLM agents
│   ├── app/
│   │   ├── api/             ← FastAPI routes (auth, projects)
│   │   ├── core/            ← Config, security
│   │   ├── models/          ← SQLAlchemy ORM models
│   │   └── schemas/         ← Pydantic schemas
│   ├── memory/              ← Persistent memory system (Phase 3)
│   │   ├── interfaces/      ← Provider ABCs
│   │   ├── embeddings/      ← Local · Ollama · HuggingFace
│   │   ├── vectorstores/    ← ChromaDB backend
│   │   ├── rag/             ← Chunker · Storage · Retrieval · Pipeline
│   │   └── utils/           ← Similarity · Chunking · Cache
│   ├── orchestrator/        ← LangGraph graph, nodes, edges, state
│   ├── prompts/             ← Agent system prompt markdown files
│   ├── tests/               ← 129 passing tests
│   ├── alembic/             ← Database migrations
│   └── requirements.txt
├── frontend/
│   ├── app/                 ← Next.js App Router pages
│   └── components/          ← React components
├── docker-compose.yml
└── README.md
```

---

## ☁️ Production Cloud Deployment

For production deployments (FastAPI on **Render**, Next.js on **Vercel**), see the [Cloud Deployment Guide](DEPLOYMENT.md).

---

## 📄 License

[MIT](LICENSE) — free for personal and commercial use.
