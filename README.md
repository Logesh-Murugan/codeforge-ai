# 🛠️ CodeForge AI

<div align="center">

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com)
[![Groq](https://img.shields.io/badge/Groq_Cloud-F55036?style=for-the-badge&logo=groq&logoColor=white)](https://groq.com)

**An enterprise-grade, multi-agent AI software developer system that designs, builds, reviews, and documents fully-functional, secure backend APIs from simple natural language descriptions.**

[System Architecture](#-system-architecture--flow) • [Key Features](#-key-technical-achievements) • [Local Setup](#-getting-started) • [Cloud Deployment](DEPLOYMENT.md)

</div>

---

## 📐 System Architecture & Flow

CodeForge AI runs a deterministic **5-Agent LangGraph state machine**. Each agent operates as a specialized role within a simulated software development team to construct, verify, and document your app:

```mermaid
flowchart TD
    A[User Prompt] --> BA[Business Analyst Agent]
    BA -->|User Stories & Entities| SA[Solution Architect Agent]
    SA -->|DB Schema & Endpoints| BD[Backend Developer Agent]
    BD -->|FastAPI Codebase| CR[Code Reviewer Agent]
    CR -->|Auto-Fixed Code| DW[Documentation Writer Agent]
    DW -->|README & Verification| DB[(PostgreSQL Store)]
    DB -->|In-Memory Compiling| ZIP[Download ZIP Archive]
```

### 👥 Meet the Developer Agents

*   **🕵️‍♂️ Business Analyst (Llama 3.1-8b)**: Analyzes user requirements to define user stories, map database entities, model constraints, and build the specification checklist.
*   **📐 Solution Architect (Llama 3.3-70b)**: Designs database schemas, relationships, indexes, and models RESTful API routes (`GET`, `POST`, `PUT`, `DELETE`).
*   **💻 Backend Developer (Llama 3.3-70b)**: Implements database connections, SQLAlchemy models, Pydantic schemas, routes, and custom operations.
*   **🔍 Code Reviewer (Llama 3.3-70b)**: Audits code for security (SQL injections, CORS limits), style guides, and **automatically applies fixes** to the codebase.
*   **✍️ Documentation Writer (Llama 3.1-8b)**: Generates a complete, professional user guide and `README.md` custom-tailored to the output codebase.

---

## 🌟 Key Technical Achievements

> [!NOTE]  
> All of these achievements are fully integrated into the code and verified via automated smoke suites.

*   **💾 Serverless-Ready Storage**: Discarded slow local disk-write actions from the code generation path. Projects are saved, updated, and queried as dynamic JSON objects inside PostgreSQL tables.
*   **⚡ In-Memory ZIP Compiling**: Utilizes Python's `zipfile` and `io.BytesIO` streams to package code bases on-the-fly and return them to users. No temporary files or cache cleanup routines are required.
*   **🌐 Render Connection Solver**: Features a custom `httpx.HTTPTransport(local_address="0.0.0.0")` engine. Bypasses dual-stack IPv6 name resolution issues, eliminating connection timeouts to Groq on Render.
*   **🧠 Robust JSON Extraction**: Cleanly splits markdown code blocks, isolates bounding `{}` characters, and parses content in non-strict mode (`strict=False`) to avoid syntax failures caused by raw newlines.

---

## 🛠️ Technology Stack

| Layer | Technology | Details |
| :--- | :--- | :--- |
| **Backend Core** | **FastAPI** | Async REST API running on Python 3.11 |
| **Orchestration** | **LangGraph** | Advanced state-machine agent controller |
| **Database** | **PostgreSQL** | Serverless Neon DB database layer |
| **Migrations** | **Alembic** | Python DB migration architecture |
| **AI Interface** | **OpenAI SDK v1.54.4** | Clean abstraction mapping Groq completions |
| **Frontend** | **Next.js 14/15** | Glassmorphic React dashboard with Tailwind CSS |

---

## 🚀 Getting Started

### Local Setup

#### 1. Backend Server Setup
```bash
# Navigate to backend
cd backend

# Install dependencies
pip install -r requirements.txt

# Create environment config
cp .env.example .env
```
Update your newly created `backend/.env` file:
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/codeforge
JWT_SECRET_KEY=generate-a-secure-key
GROQ_API_KEY=gsk_your_groq_key_here
```
Run migrations and launch the app:
```bash
# Run database migrations
alembic upgrade head

# Start FastAPI server
python -m uvicorn app.main:app --reload --port 8000
```

#### 2. Frontend Dashboard Setup
```bash
# Navigate to frontend
cd ../frontend

# Install dependencies
npm install

# Start Next.js server
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to view your premium CodeForge AI workspace!

---

### 🐳 Run Entirely with Docker Compose

Ensure **Docker Desktop** is running on your machine, then run:

```bash
# 1. Create a root .env file containing your key
echo "GROQ_API_KEY=gsk_your_key_here" > .env

# 2. Build and start PostgreSQL and Backend containers
docker-compose up --build

# 3. Start Next.js frontend locally
cd frontend
npm run dev
```

---

## 🧪 Testing & Health Checks

Verify your environment using our built-in test features:

```bash
# Run the complete agent pipeline smoke test
cd backend
python smoke_test.py
```

Check the active Groq connection from your host terminal:
```bash
curl http://127.0.0.1:8000/groq-health
```
**Response**:
```json
{
  "status": "success"
}
```

---

## ☁️ Production Cloud Deployment

For production deployments (FastAPI backend on **Render**, Next.js frontend on **Vercel**), refer to our step-by-step [Cloud Deployment Guide](DEPLOYMENT.md).