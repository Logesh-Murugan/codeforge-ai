from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from core.security import authenticate_user, create_access_token
from schemas import UserCreate
from models import User
from db import get_db
from core.config import settings

auth_router = APIRouter(
    prefix='/auth',
    tags=['auth'],
)

@auth_router.post('/register')
async def register(user: UserCreate):
    db = next(get_db())
    user_obj = await db.execute('SELECT * FROM users WHERE email = :email', {'email': user.email})
    if user_obj.first():
        raise HTTPException(status_code=400, detail='Email already registered')
    new_user = User(username=user.username, email=user.email, password_hash=await settings.PASSWORD_CONTEXT.hash(user.password))
    db.add(new_user)
    await db.commit()
    return {'message': 'User created successfully'}

@auth_router.post('/login')
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail='Invalid username or password')
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={'sub': user.id}, expires_delta=access_token_expires)
    return {'access_token': access_token, 'token_type': 'bearer'}
