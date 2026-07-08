import os
import sys
import subprocess
import time
import requests
import json
import shutil

def apply_fixes():
    app_dir = os.path.join(os.path.dirname(__file__), "extracted_app")
    print(f"[*] Applying compilation and framework fixes to {app_dir}...")
    
    # 1. Fix core/config.py (pydantic BaseSettings import)
    config_path = os.path.join(app_dir, "core", "config.py")
    with open(config_path, "r", encoding="utf-8") as f:
        config_content = f.read()
    config_content = config_content.replace(
        "from pydantic import BaseSettings",
        "from pydantic_settings import BaseSettings"
    )
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(config_content)
    print("  - Fixed core/config.py")

    # 2. Fix db.py (circular imports, define Base directly)
    db_path = os.path.join(app_dir, "db.py")
    db_code = """from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import settings

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={}
)

SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()
"""
    with open(db_path, "w", encoding="utf-8") as f:
        f.write(db_code)
    print("  - Fixed db.py")

    # 3. Fix models.py (circular imports)
    models_path = os.path.join(app_dir, "models.py")
    with open(models_path, "r", encoding="utf-8") as f:
        models_content = f.read()
    # Change 'from db import Base' -> 'from db import Base' is clean since Base is now in db.py
    # But let's verify if there is any other issue.
    # No, models.py is clean.
    print("  - Verified models.py")

    # 4. Fix core/security.py (async session import, SQLAlchemy 2.0 select syntax)
    sec_path = os.path.join(app_dir, "core", "security.py")
    sec_code = """from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import ValidationError
from jose import jwt
from core.config import settings
from schemas import UserCreate
from models import User as UserModel
from db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

pwd_context = CryptContext(schemes=['bcrypt'], default='bcrypt')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/login')

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str):
    return pwd_context.hash(password)

async def authenticate_user(db: AsyncSession, email: str, password: str):
    result = await db.execute(select(UserModel).where(UserModel.email == email))
    user = result.scalars().first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get('sub')
        if email is None:
            raise credentials_exception
        token_data = {'email': email}
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Access token expired',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    except jwt.JWTError:
        raise credentials_exception
    result = await db.execute(select(UserModel).where(UserModel.email == token_data['email']))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    return user
"""
    with open(sec_path, "w", encoding="utf-8") as f:
        f.write(sec_code)
    print("  - Fixed core/security.py")

    # 5. Fix api/auth.py (imports, password hashing, authenticate_user call signatures)
    auth_path = os.path.join(app_dir, "api", "auth.py")
    auth_code = """from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import ValidationError
from core.security import authenticate_user, create_access_token, get_password_hash
from schemas import UserCreate, User
from models import User as UserModel
from db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from core.config import settings
from sqlalchemy import select

auth_router = APIRouter(prefix="/auth", tags=["auth"])

@auth_router.post('/register', response_model=User)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserModel).where(UserModel.email == user.email))
    db_user = result.scalars().first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Email already registered'
        )
    hashed_password = get_password_hash(user.password)
    new_user = UserModel(email=user.email, username=user.username, password_hash=hashed_password, created_at=datetime.utcnow())
    db.add(new_user)
    await db.commit()
    return new_user

@auth_router.post('/login', response_model=dict)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect email or password'
        )
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={'sub': user.email}, expires_delta=access_token_expires
    )
    return {'access_token': access_token, 'token_type': 'bearer'}
"""
    with open(auth_path, "w", encoding="utf-8") as f:
        f.write(auth_code)
    print("  - Fixed api/auth.py")

    # 6. Fix api/notes.py (imports, AsyncSession, select queries)
    notes_path = os.path.join(app_dir, "api", "notes.py")
    notes_code = """from fastapi import APIRouter, Depends, HTTPException, status
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
"""
    with open(notes_path, "w", encoding="utf-8") as f:
        f.write(notes_code)
    print("  - Fixed api/notes.py")

    # 7. Add automatic table creation on startup in main.py
    main_path = os.path.join(app_dir, "main.py")
    with open(main_path, "r", encoding="utf-8") as f:
        main_content = f.read()
    
    startup_block = """
@app.on_event("startup")
async def startup():
    from db import engine, Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
"""
    if "@app.on_event" not in main_content:
        main_content += startup_block
        with open(main_path, "w", encoding="utf-8") as f:
            f.write(main_content)
    print("  - Injected database schema creation hook in main.py")

    # 8. Write .env file for generated app using SQLite
    env_path = os.path.join(app_dir, ".env")
    with open(env_path, "w", encoding="utf-8") as f:
        f.write("DATABASE_URL=sqlite+aiosqlite:///./test.db\nJWT_SECRET_KEY=adversarial-secret-key-1234567\n")
    print("  - Created .env with local SQLite DATABASE_URL")

if __name__ == "__main__":
    apply_fixes()
