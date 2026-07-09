from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from core.security import authenticate_user, create_access_token
from core.config import settings
from schemas import UserCreate, User

auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

@auth_router.post("/register")
async def register(user: UserCreate):
    user = await authenticate_user(user.email, user.password)
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    # Create new user
    return {
        "access_token": create_access_token(user.email),
        "token_type": "bearer",
    }

@auth_router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return {
        "access_token": create_access_token(user.email),
        "token_type": "bearer",
    }
