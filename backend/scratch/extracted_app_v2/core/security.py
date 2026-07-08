from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
from pydantic import ValidationError
from schemas import UserCreate
from models import User
from core.config import settings

pwd_context = CryptContext(schemes=['bcrypt'], default='bcrypt')

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str):
    return pwd_context.hash(password)

def authenticate_user(username: str, password: str):
    from db import get_db
    db = next(get_db())
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(OAuth2PasswordBearer())):
    credentials_exception = HTTPException(
        status_code=401,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get('sub')
        if username is None:
            raise credentials_exception
        token_data = username
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail='Access token expired',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    except jwt.JWTError:
        raise credentials_exception
    from db import get_db
    db = next(get_db())
    user = await db.execute(select(User).where(User.username == token_data))
    user = user.scalars().first()
    if user is None:
        raise credentials_exception
    return user
