# CodeForge AI 🚀

An advanced, enterprise-grade AI software developer system that designs, codes, reviews, and documents fully-functional, secure backend APIs from simple natural language descriptions.

CodeForge AI uses a structured **LangGraph orchestration pipeline** powered by state-of-the-art LLMs (via Groq Cloud) to automate the software development lifecycle, storing and delivering final products entirely through PostgreSQL.

---

## 🛠️ Technology Stack

| Component | Tech / Tool | Version / Details | Purpose |
| :--- | :--- | :--- | :--- |
| **Backend Framework** | **FastAPI** | Python 3.11 | High-performance asynchronous REST API |
| **AI Orchestration** | **LangGraph** | `>=0.2.0` | State-machine based multi-agent flow |
| **LLM Provider** | **Groq Cloud** | Llama 3.3-70B & 3.1-8B | High-speed, high-intelligence code generation |
| **Database** | **PostgreSQL** | Neon Serverless / Local | Persistence layer for projects, users, and code assets |
| **Database ORM** | **SQLAlchemy** | `>=2.0.20` + **asyncpg** | Asynchronous DB queries and schema declarations |
| **Migrations** | **Alembic** | `>=1.12.0` | Relational schema evolution tracking |
| **Frontend Framework**| **Next.js** | 14 / 15 (TypeScript) | Premium dashboard with live generation stepper |
| **Client Library** | **OpenAI SDK** | `1.54.4` | Standardized interface for hitting Groq endpoints |
| **HTTP Transport** | **httpx** | `0.27.2` | Under-the-hood HTTP transport with IPv4 binding |

---

## 📐 System Architecture & Flow

The system runs a deterministic 5-Agent pipeline modeled as a LangGraph state machine. Each agent specializes in one segment of the software development lifecycle (SDLC).

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

### The 5-Agent Pipeline
1. **Business Analyst (Llama 3.1-8b-instant)**: Translates user specifications into functional stories, outlines entities, maps relationships, and generates an API checklist.
2. **Solution Architect (Llama 3.3-70b-versatile)**: Transforms the BA requirements into a concrete technical architecture (SQLAlchemy tables, data types, and custom REST routes).
3. **Backend Developer (Llama 3.3-70b-versatile)**: Writes complete, compilable python files for models, schemas, config settings, router divisions, and authentication helpers.
4. **Code Reviewer (Llama 3.3-70b-versatile)**: Conducts a critical security and style audit, detects omissions or bugs, and **automatically applies code fixes** before merging.
5. **Documentation Writer (Llama 3.1-8b-instant)**: Generates a complete, professional user guide and `README.md` specific to the generated codebase.

---

## 🌟 Key Technical Achievements

### 💾 1. Serverless-Ready Database-Centric Storage
To make the application fully serverless and cloud-deployable:
* All local file system operations (writes/reads to directories like `generated_projects/`) have been removed from the active execution path.
* Generated codebases are compiled into structured JSON and stored directly in the `Project` database model.

### ⚡ 2. Zero-Disk In-Memory ZIP Streaming
When a user requests to download a generated project:
* The backend fetches the codebase JSON structure from PostgreSQL.
* It builds a valid ZIP archive completely in-memory using Python's `zipfile` module and a `io.BytesIO` buffer.
* The archive is streamed directly back as a `FileResponse` response—**no temporary folders or files are written to disk**, optimizing Render performance.

### 🌐 3. Dual-Stack Network Fallback (Render IPv6 Resolution Fix)
On strict IPv4 platforms (like Render's free tier), `httpx` DNS calls to `api.groq.com` often hang or time out due to default dual-stack IPv6 (AAAA record) connection attempts.
* **Fix**: The backend instantiates the Groq client with a custom `httpx.Client` bound explicitly to the local IPv4 address `0.0.0.0` (`transport=httpx.HTTPTransport(local_address="0.0.0.0")`), forcing smooth, fast IPv4-only routing.

### 🧠 4. Robust Error-Tolerant JSON Parser
LLMs occasionally output invalid control characters or markdown wraps that cause standard JSON decoders to crash.
* **Fix**: Implemented a parser that automatically strips code fences (````json ... ````), extracts bounding JSON braces `{ ... }`, and decodes values in non-strict mode (`strict=False`) to handle unescaped control characters.
* If a parsing failure does occur, it triggers an intelligent, auto-correcting feedback query to the model to repair and format the output.

---

## 🚀 Getting Started

### Prerequisites
* **Python**: `3.10` or `3.11`
* **Node.js**: `18+`
* **Docker Desktop** (Optional, for quick containerized database runs)

---

### Local Installation & Running

#### 1. Backend Setup
1. Change directory to `backend`:
   ```bash
   cd backend
   ```
2. Install python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up configuration variables inside `backend/.env`:
   ```env
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/codeforge
   JWT_SECRET_KEY=use-a-strong-hex-key
   GROQ_API_KEY=gsk_your_groq_key_here
   ```
4. Run migrations:
   ```bash
   alembic upgrade head
   ```
5. Start FastAPI:
   ```bash
   python -m uvicorn app.main:app --reload --port 8000
   ```

#### 2. Frontend Setup
1. In a new terminal, change to the `frontend` folder:
   ```bash
   cd frontend
   ```
2. Install npm packages:
   ```bash
   npm install
   ```
3. Create a `frontend/.env.local` file and add the API endpoint:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```
4. Start Next.js:
   ```bash
   npm run dev
   ```
5. Open [http://localhost:3000](http://localhost:3000) in your browser.

---

### 🐳 Running with Docker Compose

To spin up a PostgreSQL instance and the backend service together:

1. Create a `.env` file at the **root directory** containing your credentials:
   ```env
   GROQ_API_KEY=gsk_your_groq_key_here
   ```
2. Open Docker Desktop and run:
   ```bash
   docker-compose up --build
   ```
3. In a separate terminal, launch the Next.js dev server:
   ```bash
   cd frontend
   npm run dev
   ```

---

## 🧪 Verification & Health Check

You can run our local integration test to check that the database, migrations, and agent nodes communicate successfully:
```bash
cd backend
python smoke_test.py
```

To verify the Groq connection is functioning correctly from your host environment, hit the `/groq-health` test endpoint:
```bash
curl http://127.0.0.1:8000/groq-health
```
**Expected Response**:
```json
{
  "status": "success"
}
```

---

## ☁️ Production Cloud Deployment

* The **FastAPI Backend** is configured to run out-of-the-box on **Render** (using CORS origin filters locked by the `ALLOWED_ORIGIN` env variable).
* The **Next.js Frontend** is ready for instant deployment on **Vercel**.
* For full dashboard credentials and production steps, refer to the [Cloud Deployment Guide](DEPLOYMENT.md).