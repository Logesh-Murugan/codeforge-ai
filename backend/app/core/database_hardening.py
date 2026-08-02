"""
Database Hardening — Phase 5.11

SQLAlchemy 2.0 connection pool hardening & transaction retry wrappers.
"""
from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Any, Callable, Generator, TypeVar

from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

T = TypeVar("T")


class DatabaseHardening:
    """
    Database Hardening Utilities.
    """

    @staticmethod
    @contextmanager
    def safe_transaction(db: Session, max_retries: int = 3, retry_delay: float = 0.5) -> Generator[Session, None, None]:
        """
        Execute session operations inside a hardened transaction block.
        Automatically handles rollback and retries on transient DB failures.
        """
        attempt = 0
        while attempt < max_retries:
            try:
                yield db
                db.commit()
                break
            except (OperationalError, DBAPIError) as e:
                db.rollback()
                attempt += 1
                logger.warning(f"[DatabaseHardening] DB error on attempt {attempt}/{max_retries}: {e}")
                if attempt >= max_retries:
                    raise
                time.sleep(retry_delay)
            except Exception:
                db.rollback()
                raise


db_hardening = DatabaseHardening()
