# CodeForge AI — Memory System

> **Phase 3 complete** · Phases 3.1–3.6

A fully modular, provider-agnostic vector memory system built for the
CodeForge AI multi-agent pipeline. No OpenAI dependency. No vendor lock-in.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Embedding Providers](#embedding-providers)
5. [Vector Store](#vector-store)
6. [RAG Pipeline](#rag-pipeline)
7. [Project Memory (Phase 3.4)](#project-memory-phase-34)
8. [Agent Context Sharing (Phase 3.5)](#agent-context-sharing-phase-35)
9. [Production Hardening (Phase 3.6)](#production-hardening-phase-36)
10. [API Endpoints](#api-endpoints)
11. [Testing](#testing)
12. [Module Reference](#module-reference)

---

## Architecture Overview

```
memory/
├── interfaces/          Abstract contracts (ABCs) — no SDK imports
│   ├── embedding.py     EmbeddingProviderInterface
│   ├── vectorstore.py   VectorStoreInterface
│   └── memory.py        MemoryProviderInterface
│
├── embeddings/          Concrete embedding backends
│   ├── local.py         Hash-projection (zero-dependency fallback)
│   ├── ollama.py        Ollama REST (nomic-embed-text, 768-dim)
│   ├── huggingface.py   HuggingFace Inference API (cloud)
│   └── resolver.py      Config-driven provider selection + fallback chain
│
├── vectorstores/
│   └── chroma.py        ChromaDB persistent store (12 collections)
│
├── utils/
│   ├── similarity.py    Cosine similarity + MMR re-ranking
│   ├── chunking.py      Text chunker (character / sentence / paragraph)
│   └── cache.py         LRU embedding vector cache
│
├── rag/                 RAG pipeline (Phase 3.3)
│   ├── chunker.py       ChunkingEngine + strategies
│   ├── storage.py       StorageEngine + deduplication + versioning
│   ├── retrieval.py     RetrievalEngine + metadata filters
│   └── pipeline.py      RAGPipeline façade
│
├── context/             Agent context sharing (Phase 3.5)
│   ├── injector.py      ContextInjector + AgentRole registry
│   ├── cross_agent.py   CrossAgentMemory — shared agent bus
│   ├── long_term.py     LongTermMemory — decay-weighted retrieval
│   └── conversation.py  ConversationMemory — per-project/session buffer
│
├── schemas.py           All Pydantic data contracts
├── config.py            MemorySettings (env-var driven)
├── service.py           MemoryService — unified pipeline façade
├── manager.py           MemoryManager — wiring + lifecycle
├── project_memory.py    ProjectMemoryService (Phase 3.4)
├── cache.py             MemoryCache — TTL/LRU query result cache (Phase 3.6)
└── performance.py       PerformanceMonitor — timing + slow query log (Phase 3.6)
```

---

## Quick Start

```python
from memory import get_service

svc = get_service()   # auto-wired from env vars

# Store an artifact
svc.store_memory(
    project_id=1,
    agent_name="backend_developer",
    artifact_type="backend_code",
    collection_name="backend_code",
    content="from fastapi import FastAPI\napp = FastAPI()",
    version=1,
)

# Semantic search
results = svc.retrieve_memory(
    project_id=1,
    collection_name="backend_code",
    query="FastAPI authentication endpoint",
)

# Context injection for an agent prompt
context = svc.build_agent_context(
    project_id=1,
    agent_name="security_engineer",
    query="JWT token validation",
)
prompt += "\n\n" + context.to_prompt_block()
```

---

## Configuration

All settings are environment variables read by `MemorySettings` in
[`memory/config.py`](config.py):

| Variable                  | Default        | Description                                          |
|---------------------------|----------------|------------------------------------------------------|
| `EMBEDDING_PROVIDER`      | `local`        | `local` \| `ollama` \| `huggingface`                 |
| `EMBEDDING_FALLBACK_CHAIN`| `local`        | Comma-separated fallback list, e.g. `ollama,local`   |
| `OLLAMA_BASE_URL`         | `http://localhost:11434` | Ollama server URL                          |
| `OLLAMA_MODEL`            | `nomic-embed-text` | Model for Ollama embeddings                      |
| `HF_API_TOKEN`            | *(required for HF)* | HuggingFace Inference API key                 |
| `HF_MODEL`                | `sentence-transformers/all-MiniLM-L6-v2` | HF model  |
| `CHROMA_PATH`             | `./chroma_db`  | ChromaDB persistence directory                       |
| `MEMORY_CHUNK_SIZE`       | `800`          | Characters per chunk                                 |
| `MEMORY_CHUNK_OVERLAP`    | `100`          | Character overlap between chunks                     |
| `MEMORY_MODE`             | `local`        | `local` \| `cloud`                                   |

---

## Embedding Providers

### LocalEmbeddings (zero-dependency fallback)

Uses a deterministic hash-projection to produce 256-dim vectors. No
model download required. Suitable for testing and offline use.

```python
from memory import LocalEmbeddings
embed = LocalEmbeddings(dimension=256)
```

### OllamaEmbeddings

Calls the local Ollama REST API (`nomic-embed-text`, 768 dimensions).

```python
from memory import OllamaEmbeddings
embed = OllamaEmbeddings(base_url="http://localhost:11434")
```

### HuggingFaceEmbeddings

Calls the HuggingFace Inference API. Requires `HF_API_TOKEN`.

```python
from memory import HuggingFaceEmbeddings
embed = HuggingFaceEmbeddings(api_token="hf_...")
```

### Provider Switching at Runtime

```python
from memory import MemoryManager
manager = MemoryManager()
manager.switch_provider("ollama")   # invalidates service cache
svc = manager.get_service()
```

### Fallback Chain

Set `EMBEDDING_FALLBACK_CHAIN=ollama,local`. The resolver tries providers
in order; the first healthy one is used.

---

## Vector Store

ChromaDB with 12 pre-defined collections:

| Collection        | Agent / purpose                          |
|-------------------|------------------------------------------|
| `requirements`    | Requirements analyst outputs             |
| `architecture`    | System architecture decisions            |
| `database_design` | Schema and data model designs            |
| `api_contracts`   | REST / OpenAPI contracts                 |
| `backend_code`    | Python/FastAPI generated code            |
| `frontend_code`   | TypeScript/React generated code          |
| `security_reports`| Security engineer findings               |
| `qa_reports`      | QA test results and coverage             |
| `documentation`   | Generated docs and API specs             |
| `devops`          | Docker / k8s / CI-CD artifacts           |
| `conversation`    | Multi-turn conversation history          |
| `project_history` | Versioned artifact snapshots             |

---

## RAG Pipeline

```python
from memory.rag import RAGPipeline, RAGConfig, ChunkStrategy

pipeline = RAGPipeline.from_service(svc, config=RAGConfig(
    chunking=ChunkingConfig(chunk_size=500, strategy=ChunkStrategy.SENTENCE),
))

# Ingest
result = pipeline.ingest(
    project_id=1,
    agent_name="backend_developer",
    artifact_type="backend_code",
    collection_name="backend_code",
    content=long_source_code,
)
print(f"Ingested {result.chunks_stored} chunks")

# Retrieve
results = pipeline.retrieve(
    project_id=1,
    query="database connection pool",
    collections=["backend_code", "architecture"],
)
```

---

## Project Memory (Phase 3.4)

`ProjectMemoryService` provides a high-level API for every memory category.

```python
from memory import ProjectMemoryService

pms = ProjectMemoryService()

# Store requirements
pms.store_requirement(project_id=1, content="Users shall ...", version=1)

# Store architecture
pms.store_architecture(project_id=1, content="Microservices ...", artifact_type="architecture")

# Track generated files
pms.store_generated_file(
    project_id=1,
    file_path="backend/main.py",
    content="...",
    language="python",
)

# Record a revision
pms.record_revision(project_id=1, artifact_type="backend_code",
                    content="...", reason="Fixed auth bug", requested_by="qa")

# Full snapshot
snapshot = pms.get_project_snapshot(project_id=1)
print(f"Total artifacts: {snapshot.total_artifacts}")

# Cross-collection semantic search
results = pms.search_project_memory(project_id=1, query="JWT authentication")
```

### REST API

```
POST   /projects/{id}/memory/artifacts   Store any artifact
POST   /projects/{id}/memory/files        Track a generated file
POST   /projects/{id}/memory/revisions    Record a revision
POST   /projects/{id}/memory/search       Semantic search
GET    /projects/{id}/memory/history      Version history
GET    /projects/{id}/memory/agents/{n}   Agent memory records
GET    /projects/{id}/memory/files        Generated files list
GET    /projects/{id}/memory/revisions    Revision list
GET    /projects/{id}/memory/snapshot     Full project snapshot
DELETE /projects/{id}/memory              Wipe all memory
```

---

## Agent Context Sharing (Phase 3.5)

### ContextInjector — Role-Aware Prompt Context

```python
from memory import ContextInjector

injector = ContextInjector()

# Build a context block for a specific agent
block = injector.build_context_block(
    project_id=1,
    agent_name="backend_developer",
    user_query="implement user registration endpoint",
)
system_prompt += "\n\n" + block
```

Each agent role has pre-configured collections and a query template:

| Agent Role               | Collections searched                                |
|--------------------------|-----------------------------------------------------|
| `requirements_analyst`   | requirements, conversation, project_history          |
| `architect`              | requirements, architecture, database_design, api_contracts |
| `backend_developer`      | requirements, architecture, api_contracts, backend_code, database_design |
| `frontend_developer`     | requirements, api_contracts, frontend_code, architecture |
| `security_engineer`      | requirements, backend_code, frontend_code, api_contracts, security_reports |
| `qa_engineer`            | requirements, backend_code, frontend_code, api_contracts, qa_reports |
| `devops_engineer`        | architecture, backend_code, frontend_code, devops, documentation |

### CrossAgentMemory — Shared Agent Bus

```python
from memory import CrossAgentMemory

cam = CrossAgentMemory()

# Publish
cam.publish(project_id=1, agent_name="security_engineer",
            artifact_type="security_report", content="...", version=1)

# Read another agent's output
reports = cam.read(project_id=1, source_agent="security_engineer")
latest  = cam.read_latest(project_id=1, source_agent="security_engineer",
                          artifact_type="security_report")

# Broadcast and chain
result = cam.broadcast(project_id=1, agent_name="qa_engineer",
                       artifact_type="qa_report", content="...")
```

### LongTermMemory — Decay-Weighted Retrieval

```python
from memory import LongTermMemory

ltm = LongTermMemory(decay_rate=0.005)  # ~66% weight after 1 week

ltm.store(project_id=1, agent_name="architect",
          artifact_type="architecture", collection_name="architecture",
          content="...", importance=2.0)

results = ltm.retrieve(
    project_id=1, query="microservices design",
    collections=["architecture"], limit=5,
)
# Each result has adjusted_score = similarity * recency_weight * importance
```

### ConversationMemory — Persistent Conversation Buffer

```python
from memory import ConversationMemory

cm = ConversationMemory()

cm.append(project_id=1, role="user", content="How should I implement auth?")
cm.append(project_id=1, role="assistant", content="Use JWT with refresh tokens.")

# Retrieve history
history = cm.get_history(project_id=1, limit=20)

# Session-scoped turns
cm.append(project_id=1, role="user", content="...", session_id="tab_abc123")
tab_history = cm.get_history(project_id=1, session_id="tab_abc123")

# Summarise for prompt injection
summary = cm.summarise(project_id=1, limit=6)

# Token estimate
tokens = cm.token_estimate(project_id=1)
```

---

## Production Hardening (Phase 3.6)

### MemoryCache — TTL/LRU Query Result Cache

```python
from memory import MemoryCache

cache = MemoryCache(ttl_seconds=300, max_size=256)

# Wrap retrieve_memory with caching
results = cache.get(project_id=1, collection_name="requirements", query="auth")
if results is None:
    results = svc.retrieve_memory(project_id=1, collection_name="requirements",
                                  query="auth", limit=5)
    cache.set(project_id=1, collection_name="requirements",
              query="auth", results=results, limit=5)

# Invalidate after writes
cache.invalidate_project(project_id=1)

# Stats
print(cache.stats())
# {'size': 12, 'hits': 45, 'misses': 8, 'hit_rate': 0.849}
```

### PerformanceMonitor — Timing and Slow-Query Detection

```python
from memory import PerformanceMonitor

monitor = PerformanceMonitor(slow_threshold_ms=200)

# Decorator usage
@monitor.timed("embed_query")
def embed(text):
    ...

# Context manager
with monitor.measure("retrieve_memory"):
    results = svc.retrieve_memory(...)

# Inspect
print(monitor.summary("retrieve_memory"))
# {'count': 150, 'mean_ms': 45.2, 'p95_ms': 120.8, ...}

slow = monitor.slow_queries(threshold_ms=500)
print(monitor.throughput("embed_query"))   # ops/sec
```

---

## Testing

```bash
# From backend/ directory:

# All memory tests (excludes integration):
python -m pytest tests/test_memory.py tests/test_memory_architecture.py \
    tests/test_rag_pipeline.py tests/test_project_memory.py \
    tests/test_agent_context.py tests/test_production_hardening.py -v

# Full suite (excluding integration):
python -m pytest tests/ --ignore=tests/test_integration.py -v

# Specific phase:
python -m pytest tests/test_project_memory.py -v        # Phase 3.4
python -m pytest tests/test_agent_context.py -v         # Phase 3.5
python -m pytest tests/test_production_hardening.py -v  # Phase 3.6
```

### Test counts by phase

| Phase | Test file                        | Tests |
|-------|----------------------------------|-------|
| 3.1–3.2 | test_memory_architecture.py | 77    |
| 3.3   | test_rag_pipeline.py             | 52    |
| 3.4   | test_project_memory.py           | 69    |
| 3.5   | test_agent_context.py            | 56    |
| 3.6   | test_production_hardening.py     | ~60   |
| Legacy | test_memory.py                  | 2     |

---

## Module Reference

| Import path                             | Description                               |
|-----------------------------------------|-------------------------------------------|
| `memory.get_service()`                  | Auto-wired MemoryService singleton        |
| `memory.MemoryService`                  | Core pipeline façade                      |
| `memory.MemoryManager`                  | Provider wiring + lifecycle               |
| `memory.ProjectMemoryService`           | Project-scoped memory operations (3.4)    |
| `memory.context.ContextInjector`        | Role-aware prompt context builder (3.5)   |
| `memory.context.CrossAgentMemory`       | Shared agent memory bus (3.5)             |
| `memory.context.LongTermMemory`         | Decay-weighted retrieval (3.5)            |
| `memory.context.ConversationMemory`     | Conversation buffer (3.5)                 |
| `memory.MemoryCache`                    | TTL/LRU query result cache (3.6)          |
| `memory.PerformanceMonitor`             | Timing + slow query detection (3.6)       |
| `memory.rag.RAGPipeline`               | Full RAG pipeline (3.3)                   |
| `memory.embeddings.LocalEmbeddings`     | Zero-dep hash-projection embeddings       |
| `memory.embeddings.OllamaEmbeddings`    | Ollama nomic-embed-text embeddings        |
| `memory.embeddings.HuggingFaceEmbeddings` | HuggingFace Inference API embeddings    |
| `memory.vectorstores.ChromaVectorStore` | ChromaDB vector store backend             |
| `memory.schemas`                        | All Pydantic data contracts               |
| `memory.config.MemorySettings`          | Env-var configuration                     |
