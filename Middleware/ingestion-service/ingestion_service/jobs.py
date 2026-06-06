"""Ingestion job lifecycle, persisted in Postgres."""

from __future__ import annotations

import uuid

from anime_shared.db import session_scope
from anime_shared.exceptions import NotFoundError
from anime_shared.models import IngestionJob, JobStatus
from anime_shared.schemas import IngestionJobView


def _to_view(job: IngestionJob) -> IngestionJobView:
    return IngestionJobView(
        id=job.id,
        status=job.status.value,
        source=job.source,
        rows_processed=job.rows_processed,
        error=job.error,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


def create_job(source: str) -> IngestionJobView:
    job_id = str(uuid.uuid4())
    with session_scope() as session:
        job = IngestionJob(id=job_id, source=source, status=JobStatus.PENDING)
        session.add(job)
        session.flush()
        return _to_view(job)


def get_job(job_id: str) -> IngestionJobView:
    with session_scope() as session:
        job = session.get(IngestionJob, job_id)
        if job is None:
            raise NotFoundError(f"Ingestion job not found: {job_id}")
        return _to_view(job)


def update_job(
    job_id: str,
    *,
    status: JobStatus | None = None,
    rows_processed: int | None = None,
    error: str | None = None,
) -> None:
    with session_scope() as session:
        job = session.get(IngestionJob, job_id)
        if job is None:
            raise NotFoundError(f"Ingestion job not found: {job_id}")
        if status is not None:
            job.status = status
        if rows_processed is not None:
            job.rows_processed = rows_processed
        if error is not None:
            job.error = error
