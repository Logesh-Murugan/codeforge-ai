from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str


class User(BaseModel):
    id: int
    email: EmailStr
    username: str
    created_at: datetime

    class Config:
        orm_mode = True


class NoteCreate(BaseModel):
    title: str
    content: str


class Note(BaseModel):
    id: int
    title: str
    content: str
    author_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
