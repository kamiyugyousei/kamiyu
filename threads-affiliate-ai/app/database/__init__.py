"""Database engine, session factory, and Base."""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


def _make_engine():
    url = settings.database_url
    connect_args = {}
    if url.startswith("sqlite"):
        # ensure ./data exists for file-based sqlite
        if ":///" in url and not url.endswith(":memory:"):
            path = url.split(":///", 1)[1]
            os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
        connect_args = {"check_same_thread": False}
    return create_engine(url, connect_args=connect_args, future=True)


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    """Create all tables. Import models so they register on Base.metadata."""
    from app import models  # noqa: F401  (side-effect import)

    Base.metadata.create_all(bind=engine)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Transactional session context manager."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Iterator[Session]:
    """FastAPI dependency."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
