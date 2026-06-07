"""Worker entrypoint for ingestion — delegates to the reusable pipeline.

The heavy lifting lives in :mod:`ingestion_service.pipeline` so the same logic is
shared by the Redis worker (this path) and the Airflow DAGs.
"""

from __future__ import annotations

from anime_shared.logging import get_logger
from anime_shared.models import JobStatus

from ingestion_service import jobs, pipeline

log = get_logger("ingestion-service.runner")


def run_ingestion(job_id: str, source: str | None) -> None:
    """Run a full ingestion for ``job_id`` (records failure on the job record)."""
    try:
        pipeline.run_full_ingestion(job_id)
    except Exception as exc:  # noqa: BLE001 - already partially recorded; finalize failure
        log.exception("Ingestion job %s failed", job_id)
        jobs.update_job(job_id, status=JobStatus.FAILED, error=str(exc))
        raise
