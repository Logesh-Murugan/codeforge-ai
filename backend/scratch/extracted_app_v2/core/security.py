from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from core.config import settings
from models import User
from db import db

pwd_context = CryptContext(schemes=["bcrypt"], default="bcrypt")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def authenticate_user(email: str, password: str):
    user = await db.execute(select(User).where(User.email == email))
    user = user.scalars().first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user = await authenticate_user(token, None)
    if not user:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    return current_user

async def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

async def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

async def get_password_hash(password: str):
    return pwd_context.hash(password)
