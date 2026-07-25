from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings
from models import Base

db_url = settings.DATABASE_URL
engine = create_async_engine(db_url)

SessionLocal = sessionmaker(class_=AsyncSession, expire_on_commit=False, bind=engine)

async def get_db():
    async with SessionLocal() as db:
        yield db

async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
