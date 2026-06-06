"""The ingestion job itself: CSV -> Postgres catalog -> vector index.

Replaces the original ``pipeline/build_pipeline.py`` (which loaded a CSV and built
a Chroma store inline). Here the work is a job: it records progress in Postgres and
delegates vector indexing to vectorstore-service over HTTP.
"""

from __future__ import annotations

import httpx
from anime_shared.config import get_settings
from anime_shared.db import session_scope
from anime_shared.exceptions import DownstreamServiceError
from anime_shared.logging import get_logger
from anime_shared.models import AnimeCatalog, JobStatus
from anime_shared.schemas import IndexDocument, IndexRequest
from sqlalchemy import delete

from ingestion_service import jobs
from ingestion_service.loader import AnimeRow, load_rows

log = get_logger("ingestion-service.runner")
_INDEX_BATCH = 256


def _replace_catalog(rows: list[AnimeRow]) -> None:
    """Full refresh of the catalog table (delete-all then bulk insert)."""
    with session_scope() as session:
        session.execute(delete(AnimeCatalog))
        session.add_all(
            AnimeCatalog(
                mal_id=row.mal_id,
                name=row.name,
                score=row.score,
                genres=row.genres,
                synopsis=row.synopsis,
                combined_info=row.combined_info,
            )
            for row in rows
        )


def _index_documents(rows: list[AnimeRow]) -> None:
    settings = get_settings()
    url = settings.vectorstore_service_url.rstrip("/") + "/index"
    try:
        with httpx.Client(timeout=120) as client:
            for start in range(0, len(rows), _INDEX_BATCH):
                batch = rows[start : start + _INDEX_BATCH]
                documents = [
                    IndexDocument(
                        id=str(row.mal_id) if row.mal_id is not None else f"row-{start + i}",
                        text=row.combined_info,
                        metadata=row.metadata,
                    )
                    for i, row in enumerate(batch)
                ]
                resp = client.post(url, json=IndexRequest(documents=documents).model_dump())
                resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise DownstreamServiceError("vectorstore-service /index failed", cause=exc) from exc


def run_ingestion(job_id: str, source: str | None) -> None:
    """Execute one ingestion job end to end, recording status in Postgres."""
    log.info("Starting ingestion job %s (source=%s)", job_id, source)
    jobs.update_job(job_id, status=JobStatus.RUNNING)
    try:
        rows = load_rows(source)
        _replace_catalog(rows)
        _index_documents(rows)
        jobs.update_job(job_id, status=JobStatus.COMPLETED, rows_processed=len(rows))
        log.info("Ingestion job %s completed (%d rows)", job_id, len(rows))
    except Exception as exc:  # noqa: BLE001 - record failure on the job record
        log.exception("Ingestion job %s failed", job_id)
        jobs.update_job(job_id, status=JobStatus.FAILED, error=str(exc))
        raise
