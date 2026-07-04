import os
from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    GROQ_API_KEY: str
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    @model_validator(mode="before")
    @classmethod
    def check_and_map_keys(cls, data: dict) -> dict:
        # Prioritize JWT_SECRET environment variable, fallback to JWT_SECRET_KEY
        jwt_sec = os.getenv("JWT_SECRET") or os.getenv("JWT_SECRET_KEY") or data.get("JWT_SECRET_KEY")
        if jwt_sec:
            data["JWT_SECRET_KEY"] = jwt_sec

        # Fail loudly on startup if missing critical keys
        db_url = os.getenv("DATABASE_URL") or data.get("DATABASE_URL")
        groq_key = os.getenv("GROQ_API_KEY") or data.get("GROQ_API_KEY")

        if not db_url:
            raise ValueError("DATABASE_URL environment variable is missing!")
        if not jwt_sec:
            raise ValueError("JWT_SECRET (or JWT_SECRET_KEY) environment variable is missing!")
        if not groq_key:
            raise ValueError("GROQ_API_KEY environment variable is missing!")

        return data

    class Config:
        env_file = ".env"


settings = Settings()
