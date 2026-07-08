from fastapi import APIRouter, Depends, HTTPException
from core.security import get_password_hash, verify_password
from core.config import settings
from db import get_db
from models import User
from schemas import UserCreate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import jwt
from typing import Optional

router = APIRouter(
    prefix='/auth',
    tags=['auth'],
)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

async def get_user(db: AsyncSession, username: str):
    result = await db.execute(select(User).where(User.username == username))
    return result.scalars().first()

@router.post('/register', response_model=User)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    user_db = await get_user(db, user.username)
    if user_db:
        raise HTTPException(status_code=400, detail='Email or username already registered')
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, username=user.username, password_hash=hashed_password, created_at=datetime.utcnow())
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

@router.post('/login', response_model=Token)
async def login(form_data: dict, db: AsyncSession = Depends(get_db)):
    user_db = await get_user(db, form_data['username'])
    if not user_db:
        raise HTTPException(status_code=401, detail='Incorrect username or password')
    if not verify_password(form_data['password'], user_db.password_hash):
        raise HTTPException(status_code=401, detail='Incorrect username or password')
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={'sub': user_db.username}, expires_delta=access_token_expires
    )
    return {'access_token': access_token, 'token_type': 'bearer'}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt
