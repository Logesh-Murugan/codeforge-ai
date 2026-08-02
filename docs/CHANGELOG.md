# CHANGELOG — CodeForge AI

## [v2.0.0] - 2026-08-02
### Added
- Phase 5.11: Production Hardening & Release Engineering pass.
- Database connection pool recycling (`pool_recycle=3600`), pre-ping, retry transaction context manager.
- Request correlation ID middleware (`X-Correlation-ID`) & execution time headers.
- Security hardening: Path traversal protection, Zip Slip safety, prompt injection detection.
- Production Health & Diagnostic APIs (`/health`, `/health/liveness`, `/health/readiness`, `/health/diagnostics`).
- Full system documentation suite (`docs/ARCHITECTURE.md`, `DEVELOPER_GUIDE.md`, `DEPLOYMENT_GUIDE.md`, `API_GUIDE.md`, `RELEASE_NOTES_v2.0.0.md`).

### Completed Phases
- Phase 1: Core Platform & Setup
- Phase 2: Multi-Agent Workflow Engine (13 Agents)
- Phase 3: Hybrid RAG Architecture
- Phase 4: Export Engine, Testing Engine, Validation Engine
- Phase 5.1: Tiered Memory Manager
- Phase 5.2: Knowledge Manager
- Phase 5.3: RAG Pipeline
- Phase 5.4: Retrieval Engine
- Phase 5.5: Context Sharing Engine
- Phase 5.6: AI Mode Manager (Ollama / Groq)
- Phase 5.7: Real-Time Monitoring System
- Phase 5.8: Validation Pipeline Quality Gate (12 Stages)
- Phase 5.9: Project Timeline System (9 Milestones)
- Phase 5.10: Portfolio Output System (8 Mermaid Diagrams & ZIP Bundler)
- Phase 5.11: Production Hardening & Release Engineering (v2.0.0)
