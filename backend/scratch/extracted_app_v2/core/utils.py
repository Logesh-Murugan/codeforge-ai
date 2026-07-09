from sqlalchemy.ext.asyncio import AsyncSession
from db import SessionLocal


async def get_db():
    """
    Returns a database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()