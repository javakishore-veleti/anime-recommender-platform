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
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AnimeCatalog(Base):
    """One row per anime title, loaded from the source dataset by ingestion."""

    __tablename__ = "anime_catalog"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mal_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(512), index=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    genres: Mapped[str | None] = mapped_column(Text, nullable=True)
    synopsis: Mapped[str | None] = mapped_column(Text, nullable=True)
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


class User(Base):
    """Scaffold for portal users (auth not yet implemented)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    saved_recommendations: Mapped[list["SavedRecommendation"]] = relationship(
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
