from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from core.security import authenticate_user, create_access_token
from core.utils import get_db
from models import User
from schemas import UserCreate, User
from datetime import timedelta


auth_router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@auth_router.post("/register")
def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = User(email=user.email, username=user.username, password_hash=authenticate_user(user.email, user.password, db))
    db.add(db_user)
    await db.commit()
    return {"message": "User created successfully"}

@auth_router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}