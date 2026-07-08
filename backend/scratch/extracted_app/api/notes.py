from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from core.security import get_current_user
from schemas import NoteCreate, Note
from models import Note as NoteModel, User as UserModel
from db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

notes_router = APIRouter(prefix="/notes", tags=["notes"])

@notes_router.post('/', response_model=Note)
async def create_note(note: NoteCreate, db: AsyncSession = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    new_note = NoteModel(title=note.title, content=note.content, author_id=current_user.id, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    db.add(new_note)
    await db.commit()
    return new_note

@notes_router.get('/{note_id}', response_model=Note)
async def get_note(note_id: int, db: AsyncSession = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    result = await db.execute(select(NoteModel).where(NoteModel.id == note_id))
    note = result.scalars().first()
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Note not found'
        )
    if note.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You do not own this note'
        )
    return note

@notes_router.get('/', response_model=list[Note])
async def get_notes(db: AsyncSession = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    result = await db.execute(select(NoteModel).where(NoteModel.author_id == current_user.id))
    notes = result.scalars().all()
    return notes

@notes_router.put('/{note_id}', response_model=Note)
async def update_note(note_id: int, note: NoteCreate, db: AsyncSession = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    result = await db.execute(select(NoteModel).where(NoteModel.id == note_id))
    existing_note = result.scalars().first()
    if not existing_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Note not found'
        )
    if existing_note.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You do not own this note'
        )
    existing_note.title = note.title
    existing_note.content = note.content
    await db.commit()
    return existing_note

@notes_router.delete('/{note_id}')
async def delete_note(note_id: int, db: AsyncSession = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    result = await db.execute(select(NoteModel).where(NoteModel.id == note_id))
    note = result.scalars().first()
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Note not found'
        )
    if note.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You do not own this note'
        )
    await db.delete(note)
    await db.commit()
    return {'message': 'Note deleted successfully'}
