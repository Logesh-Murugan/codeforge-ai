from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from core.security import get_current_user
from schemas import NoteCreate, Note
from models import Note as NoteModel
from db import get_db
from core.config import settings

router = APIRouter(
    prefix="/notes",
    tags=["notes"],
)

@router.post("/")
async def create_note(note: NoteCreate, current_user: UserModel = Depends(get_current_user)):
    db = next(get_db())
    new_note = NoteModel(content=note.content, author_id=current_user.id)
    db.add(new_note)
    await db.commit()
    return {
        "message": "Note created successfully"
    }

@router.get("/{note_id}")
async def get_note(note_id: int, current_user: UserModel = Depends(get_current_user)):
    db = next(get_db())
    note_obj = await db.execute(select(NoteModel).where(NoteModel.id == note_id).where(NoteModel.author_id == current_user.id))
    note = note_obj.scalars().first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return Note.from_orm(note)

@router.get("/")
async def get_notes(current_user: UserModel = Depends(get_current_user)):
    db = next(get_db())
    notes_obj = await db.execute(select(NoteModel).where(NoteModel.author_id == current_user.id))
    notes = notes_obj.scalars().all()
    return [Note.from_orm(note) for note in notes]

@router.put("/{note_id}")
async def update_note(note_id: int, note: NoteCreate, current_user: UserModel = Depends(get_current_user)):
    db = next(get_db())
    note_obj = await db.execute(select(NoteModel).where(NoteModel.id == note_id).where(NoteModel.author_id == current_user.id))
    note_to_update = note_obj.scalars().first()
    if not note_to_update:
        raise HTTPException(status_code=404, detail="Note not found")
    note_to_update.content = note.content
    await db.commit()
    return {
        "message": "Note updated successfully"
    }

@router.delete("/{note_id}")
async def delete_note(note_id: int, current_user: UserModel = Depends(get_current_user)):
    db = next(get_db())
    note_obj = await db.execute(select(NoteModel).where(NoteModel.id == note_id).where(NoteModel.author_id == current_user.id))
    note_to_delete = note_obj.scalars().first()
    if not note_to_delete:
        raise HTTPException(status_code=404, detail="Note not found")
    await db.delete(note_to_delete)
    await db.commit()
    return {
        "message": "Note deleted successfully"
    }
