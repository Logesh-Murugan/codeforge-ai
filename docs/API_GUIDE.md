# CodeForge AI — OpenAPI & REST Endpoints Reference (v2.0.0)

## System Endpoints Map

### Health & Diagnostics
- `GET /health`: System-wide aggregated health status.
- `GET /health/liveness`: Kubernetes liveness probe.
- `GET /health/readiness`: Kubernetes readiness probe.
- `GET /health/diagnostics`: Detailed platform diagnostics & telemetry.

### AI Mode Manager (`/ai-mode/*`)
- `GET /ai-mode/config`: Active provider & model configuration.
- `POST /ai-mode/switch`: Switch provider mode (`LOCAL` vs `CLOUD`).

### Real-Time Monitoring (`/monitoring/*`)
- `GET /monitoring/active-workflows`: Currently running multi-agent workflows.
- `GET /ws/monitoring`: Real-time WebSocket telemetry stream.

### Validation Pipeline (`/validation/*`)
- `POST /validation/run`: Trigger 12-stage validation quality gate.
- `GET /validation/latest`: Retrieve latest validation inspection result.

### Project Timeline (`/timeline/*`)
- `GET /timeline/{project_id}`: Full chronological timeline events.
- `GET /timeline/milestones/{project_id}`: Milestone achievements.
- `GET /timeline/analytics/{project_id}`: Performance analytics breakdown.

### Portfolio Output Package (`/portfolio/*`)
- `GET /portfolio/{project_id}`: Full portfolio package payload.
- `GET /portfolio/download/{project_id}`: Download complete portfolio ZIP archive.
- `GET /portfolio/architecture/{project_id}`: Mermaid diagrams & architecture docs.
