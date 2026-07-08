from fastapi import APIRouter, Depends, HTTPException, status
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
