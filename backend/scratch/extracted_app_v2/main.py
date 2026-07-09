from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from api.auth import auth_router
from api.notes import notes_router

app = FastAPI(
    title=settings.PROJECT_TITLE,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
)

app.include_router(auth_router)
app.include_router(notes_router)

origins = [
    "http://localhost:8000",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    from db import engine, Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
