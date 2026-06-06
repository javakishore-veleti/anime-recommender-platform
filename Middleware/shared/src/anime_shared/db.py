"""SQLAlchemy engine/session management (lazily initialized, shared across services)."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from anime_shared.config import get_settings
from anime_shared.models import Base

_engine: Engine | None = None
_SessionFactory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """Return the process-wide SQLAlchemy engine, creating it on first use."""
    global _engine, _SessionFactory
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
        _SessionFactory = sessionmaker(bind=_engine, expire_on_commit=False, future=True)
    return _engine


def create_all() -> None:
    """Create all tables. Convenient for local dev; use migrations in production."""
    Base.metadata.create_all(get_engine())


@contextmanager
def session_scope() -> Iterator[Session]:
    """Transactional session scope: commit on success, rollback on error."""
    get_engine()
    assert _SessionFactory is not None
    session = _SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding a session (caller controls the transaction)."""
    get_engine()
    assert _SessionFactory is not None
    session = _SessionFactory()
    try:
        yield session
    finally:
        session.close()
