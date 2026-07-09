from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_TITLE: str = "FastAPI Project"
    PROJECT_DESCRIPTION: str = "A FastAPI project"
    PROJECT_VERSION: str = "1.0.0"
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/dbname"
    JWT_SECRET_KEY: str = "your-secret-key-here"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
