# CodeForge AI — Developer & Contributor Guide (v2.0.0)

## Quick Start

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- Docker Desktop (optional, for containerized run)

### 2. Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 4. Running Test Suite
```bash
cd backend
python scratch/verify_release_v2_suite.py
```
