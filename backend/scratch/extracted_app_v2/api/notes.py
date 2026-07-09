from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
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
async def create_note(note: NoteCreate, db = Depends(get_db), current_user = Depends(get_current_user)):
    new_note = NoteModel(content=note.content, author_id=current_user.id)
    db.add(new_note)
    await db.commit()
    return {'message': 'Note created successfully'}

@notes_router.get('/{note_id}')
async def get_note(note_id: int, db = Depends(get_db), current_user = Depends(get_current_user)):
    note = await db.execute('SELECT * FROM notes WHERE id = :id AND author_id = :author_id', {'id': note_id, 'author_id': current_user.id})
    note_obj = note.first()
    if not note_obj:
        raise HTTPException(status_code=404, detail='Note not found')
    return Note(id=note_obj.id, content=note_obj.content, author_id=note_obj.author_id, created_at=note_obj.created_at, updated_at=note_obj.updated_at)

@notes_router.get('/')
async def get_notes(db = Depends(get_db), current_user = Depends(get_current_user)):
    notes = await db.execute('SELECT * FROM notes WHERE author_id = :author_id', {'author_id': current_user.id})
    return [Note(id=note.id, content=note.content, author_id=note.author_id, created_at=note.created_at, updated_at=note.updated_at) for note in notes]

@notes_router.put('/{note_id}')
async def update_note(note_id: int, note: NoteCreate, db = Depends(get_db), current_user = Depends(get_current_user)):
    note_obj = await db.execute('SELECT * FROM notes WHERE id = :id AND author_id = :author_id', {'id': note_id, 'author_id': current_user.id})
    note_obj = note_obj.first()
    if not note_obj:
        raise HTTPException(status_code=404, detail='Note not found')
    note_obj.content = note.content
    await db.commit()
    return {'message': 'Note updated successfully'}

@notes_router.delete('/{note_id}')
async def delete_note(note_id: int, db = Depends(get_db), current_user = Depends(get_current_user)):
    note = await db.execute('SELECT * FROM notes WHERE id = :id AND author_id = :author_id', {'id': note_id, 'author_id': current_user.id})
    note_obj = note.first()
    if not note_obj:
        raise HTTPException(status_code=404, detail='Note not found')
    await db.delete(note_obj)
    await db.commit()
    return {'message': 'Note deleted successfully'}
