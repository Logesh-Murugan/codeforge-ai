from fastapi import APIRouter, Depends, HTTPException
from core.security import get_current_user
from core.config import settings
from db import get_db
from models import Note
from schemas import NoteCreate, Note
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(
    prefix='/notes',
    tags=['notes'],
)

async def get_note(db: AsyncSession, note_id: int):
    result = await db.execute(select(Note).where(Note.id == note_id))
    return result.scalars().first()

@router.post('/', response_model=Note)
async def create_note(note: NoteCreate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    db_note = Note(title=note.title, content=note.content, author_id=current_user['id'], created_at=datetime.utcnow())
    db.add(db_note)
    await db.commit()
    await db.refresh(db_note)
    return db_note

@router.get('/{note_id}', response_model=Note)
async def read_note(note_id: int, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    note_db = await get_note(db, note_id)
    if not note_db:
        raise HTTPException(status_code=404, detail='Note not found')
    if note_db.author_id != current_user['id']:
        raise HTTPException(status_code=403, detail='You do not own this note')
    return note_db

@router.get('/', response_model=list[Note])
async def read_notes(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    result = await db.execute(select(Note).where(Note.author_id == current_user['id']))
    return result.scalars().all()

@router.put('/{note_id}', response_model=Note)
async def update_note(note_id: int, note: NoteCreate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    note_db = await get_note(db, note_id)
    if not note_db:
        raise HTTPException(status_code=404, detail='Note not found')
    if note_db.author_id != current_user['id']:
        raise HTTPException(status_code=403, detail='You do not own this note')
    note_db.title = note.title
    note_db.content = note.content
    note_db.updated_at = datetime.utcnow()
    db.add(note_db)
    await db.commit()
    await db.refresh(note_db)
    return note_db

@router.delete('/{note_id}')
async def delete_note(note_id: int, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    note_db = await get_note(db, note_id)
    if not note_db:
        raise HTTPException(status_code=404, detail='Note not found')
    if note_db.author_id != current_user['id']:
        raise HTTPException(status_code=403, detail='You do not own this note')
    await db.delete(note_db)
    await db.commit()
