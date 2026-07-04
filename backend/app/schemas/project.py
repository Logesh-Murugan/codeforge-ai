from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ProjectCreate(BaseModel):
    title: str
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    id: int
    owner_id: int
    title: str
    description: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
