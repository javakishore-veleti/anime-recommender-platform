"""SQLAlchemy engine/session management (lazily initialized, shared across services)."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from anime_shared.config import get_settings
from anime_shared.logging import get_logger
from anime_shared.models import Base

log = get_logger("anime_shared.db")

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


def _ensure_database() -> None:
    """Create the target database if it does not exist.

    We never hardcode a specific server — we use whatever DATABASE_URL points at.
    To create a database you must be connected to a *different* one, so we connect
    to the always-present ``postgres`` maintenance database to issue CREATE DATABASE.
    No-op for non-PostgreSQL URLs or when the target already exists.
    """
    settings = get_settings()
    url = make_url(settings.database_url)
    if not url.drivername.startswith("postgresql"):
        return
    target = url.database
    if not target or target == "postgres":
        return  # the default maintenance DB always exists
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT", future=True)
    try:
        with admin.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": target}
            ).scalar()
            if not exists:
                log.info("Creating database %s", target)
                conn.execute(text(f'CREATE DATABASE "{target}"'))
    finally:
        admin.dispose()


def create_all() -> None:
    """Bootstrap the database for local dev: ensure DB + schema exist, then tables.

    1. create the target database if missing,
    2. create the configured schema (default ``anime``) inside it,
    3. create all tables in that schema.
    Use Alembic migrations in production instead.
    """
    settings = get_settings()
    schema = settings.db_schema
    engine = get_engine()

    # All services bootstrap concurrently, and `CREATE SCHEMA IF NOT EXISTS` /
    # table creation are NOT atomic across connections in Postgres — two starters
    # can race and one raises "already exists". These steps are idempotent in
    # intent, so we treat such races as success: log and verify, never crash.
    try:
        _ensure_database()
        if schema:
            with engine.begin() as conn:
                conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
        Base.metadata.create_all(engine)
    except SQLAlchemyError as exc:
        # Verify the end state actually exists; if so, the error was just a race.
        try:
            inspector = inspect(engine)
            schemas = inspector.get_schema_names()
            if (not schema or schema in schemas) and inspector.get_table_names(schema=schema):
                log.warning("create_all race ignored (objects already present): %s", exc)
                return
        except SQLAlchemyError:
            pass
        raise


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
