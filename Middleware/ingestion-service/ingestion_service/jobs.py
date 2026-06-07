"""Ingestion job lifecycle, persisted in Postgres."""

from __future__ import annotations

import uuid

from anime_shared.db import session_scope
from anime_shared.exceptions import NotFoundError
from anime_shared.models import IngestionBatch, IngestionJob, JobStatus
from anime_shared.schemas import IngestionBatchView, IngestionJobView


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


# ---- per-concept batch tracking ---------------------------------------------

def create_batch(job_id: str, concept: str, batch_index: int) -> int:
    with session_scope() as session:
        batch = IngestionBatch(
            job_id=job_id, concept=concept, batch_index=batch_index, status=JobStatus.PENDING
        )
        session.add(batch)
        session.flush()
        return batch.id


def update_batch(
    batch_id: int,
    *,
    status: JobStatus | None = None,
    rows: int | None = None,
    error: str | None = None,
) -> None:
    with session_scope() as session:
        batch = session.get(IngestionBatch, batch_id)
        if batch is None:
            return
        if status is not None:
            batch.status = status
        if rows is not None:
            batch.rows = rows
        if error is not None:
            batch.error = error


def list_batches(job_id: str) -> list[IngestionBatchView]:
    from sqlalchemy import select

    with session_scope() as session:
        rows = session.scalars(
            select(IngestionBatch)
            .where(IngestionBatch.job_id == job_id)
            .order_by(IngestionBatch.batch_index)
        ).all()
        return [
            IngestionBatchView(
                concept=b.concept,
                batch_index=b.batch_index,
                rows=b.rows,
                status=b.status.value,
            )
            for b in rows
        ]
