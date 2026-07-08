from pydantic import BaseModel
from datetime import datetime

class UserCreate(BaseModel):
    email: str
    username: str
    password: str

class User(BaseModel):
    id: int
    email: str
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
