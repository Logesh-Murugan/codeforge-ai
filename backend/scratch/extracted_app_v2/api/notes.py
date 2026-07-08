from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import ValidationError
from core.security import get_current_user
from schemas import NoteCreate, Note
from models import Note as NoteModel
from db import get_db
from core.config import settings

notes_router = APIRouter(
    prefix='/notes',
    tags=['notes'],
)

@notes_router.post('/')
async def create_note(note: NoteCreate, current_user: User = Depends(get_current_user)):
    db = next(get_db())
    note_obj = NoteModel(content=note.content, author_id=current_user.id)
    db.add(note_obj)
    await db.commit()
    return {'message': 'Note created successfully'}

@notes_router.get('/{note_id}')
async def get_note(note_id: int, current_user: User = Depends(get_current_user)):
    db = next(get_db())
    note = await db.execute(select(NoteModel).where(NoteModel.id == note_id, NoteModel.author_id == current_user.id))
    note = note.scalars().first()
    if not note:
        raise HTTPException(
            status_code=404,
            detail='Note not found',
        )
    return Note.from_orm(note)

@notes_router.get('/')
async def get_notes(current_user: User = Depends(get_current_user)):
    db = next(get_db())
    notes = await db.execute(select(NoteModel).where(NoteModel.author_id == current_user.id))
    notes = notes.scalars().all()
    return [Note.from_orm(note) for note in notes]

@notes_router.put('/{note_id}')
async def update_note(note_id: int, note: NoteCreate, current_user: User = Depends(get_current_user)):
    db = next(get_db())
    note_obj = await db.execute(select(NoteModel).where(NoteModel.id == note_id, NoteModel.author_id == current_user.id))
    note_obj = note_obj.scalars().first()
    if not note_obj:
        raise HTTPException(
            status_code=404,
            detail='Note not found',
        )
    note_obj.content = note.content
    await db.commit()
    return {'message': 'Note updated successfully'}

@notes_router.delete('/{note_id}')
async def delete_note(note_id: int, current_user: User = Depends(get_current_user)):
    db = next(get_db())
    note = await db.execute(select(NoteModel).where(NoteModel.id == note_id, NoteModel.author_id == current_user.id))
    note = note.scalars().first()
    if not note:
        raise HTTPException(
            status_code=404,
            detail='Note not found',
        )
    await db.delete(note)
    await db.commit()
    return {'message': 'Note deleted successfully'}
