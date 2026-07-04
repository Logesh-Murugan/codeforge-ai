from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, projects

app = FastAPI(title="CodeForge AI Backend")

import os

allowed_origin = os.getenv("ALLOWED_ORIGIN", "http://localhost:3000")
allow_origins = [allowed_origin]
if allowed_origin != "http://localhost:3000":
    allow_origins.extend(["http://localhost:3000", "http://127.0.0.1:3000"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)


@app.get("/")
async def root():
    return {"message": "CodeForge AI Backend"}
