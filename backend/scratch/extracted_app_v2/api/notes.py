from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from core.security import get_current_user
from core.config import settings
from schemas import NoteCreate, Note
from models import Note
from db import db

notes_router = APIRouter(
    prefix="/notes",
    tags=["notes"],
)

@notes_router.post("/")
async def create_note(note: NoteCreate, current_user: User = Depends(get_current_user)):
    note = Note(content=note.content, author_id=current_user.id)
    db.add(note)
    await db.commit()
    return note

@notes_router.get("/")
async def read_notes(current_user: User = Depends(get_current_user)):
    notes = await db.execute(select(Note).where(Note.author_id == current_user.id))
    return notes.scalars().all()

@notes_router.get("/{note_id}")
async def read_note(note_id: int, current_user: User = Depends(get_current_user)):
    note = await db.execute(select(Note).where(Note.id == note_id).where(Note.author_id == current_user.id))
    note = note.scalars().first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

@notes_router.patch("/{note_id}")
async def update_note(note_id: int, note: NoteCreate, current_user: User = Depends(get_current_user)):
    note_obj = await db.execute(select(Note).where(Note.id == note_id).where(Note.author_id == current_user.id))
    note_obj = note_obj.scalars().first()
    if not note_obj:
        raise HTTPException(status_code=404, detail="Note not found")
    note_obj.content = note.content
    await db.commit()
    return note_obj

@notes_router.delete("/{note_id}")
async def delete_note(note_id: int, current_user: User = Depends(get_current_user)):
    note = await db.execute(select(Note).where(Note.id == note_id).where(Note.author_id == current_user.id))
    note = note.scalars().first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    await db.delete(note)
    await db.commit()
    return {"message": "Note deleted"}
