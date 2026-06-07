"""SQLAlchemy 2.0 ORM models.

The original demo had no relational store (CSV + file-based Chroma only). This
introduces a Postgres-backed catalog plus ingestion-job tracking, and scaffolds
user / saved-recommendation tables for future portal features.
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from anime_shared.config import get_settings

# All tables live in a dedicated schema (default "anime") so the platform can
# share a database with other projects without colliding. None => default schema.
_SCHEMA = get_settings().db_schema or None


class Base(DeclarativeBase):
    """Declarative base for all ORM models (namespaced to the configured schema)."""

    metadata = MetaData(schema=_SCHEMA)


class JobStatus(enum.StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AnimeCatalog(Base):
    """One row per anime title.

    Populated by the ingestion service from an ORIGINAL, fully synthetic generator
    (no third-party data) — see ingestion_service.generator. Fields support both
    the recommender (combined_info → embeddings) and the browse/detail UI.
    """

    __tablename__ = "anime_catalog"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(512), index=True)
    synopsis: Mapped[str | None] = mapped_column(Text, nullable=True)
    genres: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    episodes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    studio: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    combined_info: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IngestionJob(Base):
    """Tracks a single ingestion run (CSV -> Postgres + vector index)."""

    __tablename__ = "ingestion_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status"), default=JobStatus.PENDING, index=True
    )
    source: Mapped[str] = mapped_column(String(512))
    rows_processed: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class IngestionBatch(Base):
    """One concept/category batch within an ingestion job (per-batch tracking)."""

    __tablename__ = "ingestion_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(
        ForeignKey("ingestion_jobs.id", ondelete="CASCADE"), index=True
    )
    concept: Mapped[str] = mapped_column(String(64), index=True)
    batch_index: Mapped[int] = mapped_column(Integer, default=0)
    rows: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="batch_status"), default=JobStatus.PENDING, index=True
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class User(Base):
    """Scaffold for portal users (auth not yet implemented)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    saved_recommendations: Mapped[list[SavedRecommendation]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class SavedRecommendation(Base):
    """A recommendation a user chose to save."""

    __tablename__ = "saved_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    query: Mapped[str] = mapped_column(Text)
    response: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="saved_recommendations")
