"""
conftest.py — Backend root pytest configuration.

Fixes: RuntimeError: Event loop is closed
Cause: The global AsyncEngine in app/db.py uses a connection pool (AsyncAdaptedQueuePool).
       Under pytest-asyncio strict mode, each test gets its own function-scoped event loop.
       Pool connections created on one event loop cannot be safely reused on another, causing:
         RuntimeError: Event loop is closed
         RuntimeWarning: coroutine 'Connection._cancel' was never awaited

Fix:   For each test that uses the database, replace the global engine with a fresh
       NullPool-backed engine. NullPool creates a raw connection per session and discards
       it immediately — no connections are ever held across event loops.

Production behavior (uvicorn, Docker): unaffected. conftest.py is only loaded by pytest.
"""
import pytest
import pytest_asyncio

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings


@pytest.fixture(autouse=True)
def patch_db_engine(monkeypatch):
    """
    Replace the global engine and AsyncSessionLocal in app.db with a NullPool-backed
    engine for every test. NullPool never reuses connections across event loops, which
    eliminates 'Event loop is closed' errors from asyncpg under pytest-asyncio strict mode.

    autouse=True ensures this runs for every test in the backend suite without requiring
    any test to explicitly request it.
    """
    import app.db as db_module

    test_engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )
    test_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    monkeypatch.setattr(db_module, "engine", test_engine)
    monkeypatch.setattr(db_module, "AsyncSessionLocal", test_session_factory)

    # Also patch any modules that have already imported AsyncSessionLocal directly
    import app.api.export as export_mod
    import app.api.validate as validate_mod
    import app.api.testing as testing_mod
    try:
        monkeypatch.setattr(export_mod, "AsyncSessionLocal", test_session_factory)
    except AttributeError:
        pass
    try:
        monkeypatch.setattr(validate_mod, "AsyncSessionLocal", test_session_factory)
    except AttributeError:
        pass
    try:
        monkeypatch.setattr(testing_mod, "AsyncSessionLocal", test_session_factory)
    except AttributeError:
        pass

    yield
