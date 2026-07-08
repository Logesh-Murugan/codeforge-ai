from passlib.context import CryptContext
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
