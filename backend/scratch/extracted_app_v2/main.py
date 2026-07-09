from fastapi import FastAPI\nfrom fastapi.middleware.cors import CORSMiddleware\nfrom core.config import settings\nfrom api.auth import auth_router\nfrom api.notes import notes_router\n\napp = FastAPI(\n    title=settings.PROJECT_TITLE,\n    description=settings.PROJECT_DESCRIPTION,\n    version=settings.PROJECT_VERSION,\n    openapi_url=f"/{settings.API_V1_STR}/openapi.json"\n)\n\norigins = [\n    "*://localhost:8000",\n    "http://localhost:8000"\n]\n\napp.add_middleware(\n    CORSMiddleware,\n    allow_origins=origins,\n    allow_credentials=True,\n    allow_methods=["*"],\n    allow_headers=["*"],\n)\n\napp.include_router(auth_router, prefix="/auth")\napp.include_router(notes_router, prefix="/notes")
@app.on_event("startup")
async def startup():
    from db import engine, Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
