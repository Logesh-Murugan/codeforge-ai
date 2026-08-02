# CodeForge AI — Production Deployment Guide (v2.0.0)

## Containerized Deployment (Docker Compose)

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - ALLOWED_ORIGIN=http://localhost:3000
      - AI_PROVIDER_MODE=GROQ
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/liveness"]
      interval: 10s
      timeout: 5s
      retries: 3
```

## Kubernetes Probes Specification

- **Liveness Probe**: `GET /health/liveness` (Port 8000)
- **Readiness Probe**: `GET /health/readiness` (Port 8000)
- **Diagnostics**: `GET /health/diagnostics` (Port 8000)
