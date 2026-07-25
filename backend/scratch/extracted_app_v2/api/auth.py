from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from core.security import authenticate_user, create_access_token
from schemas import UserCreate, User
from models import User as UserModel
from db import get_db
from core.config import settings

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

@router.post("/register")
async def register(user: UserCreate):
    db = next(get_db())
    user_obj = await db.execute(select(UserModel).where(UserModel.email == user.email))
    if user_obj.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = UserModel(email=user.email, username=user.username, password_hash=await hash_password(user.password))
    db.add(new_user)
    await db.commit()
    return {
        "message": "User created successfully"
    }

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
