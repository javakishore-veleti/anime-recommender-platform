"""Background worker: consume ingestion job ids from Redis and run them.

A simple, dependency-free broker (Redis list + BLPOP). Run via
``python -m app.worker`` or ``npm run dev:ingestion-worker``.
"""

from __future__ import annotations

import signal
import sys

from anime_shared.db import create_all
from anime_shared.logging import get_logger, setup_logging
from anime_shared.redis_client import dequeue_job

from ingestion_service.runner import run_ingestion

log = get_logger("ingestion-service.worker")
_running = True


def _stop(*_: object) -> None:
    global _running
    log.info("Worker shutting down...")
    _running = False


def main() -> int:
    setup_logging("ingestion-service.worker")
    create_all()
    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)
    log.info("Ingestion worker started; waiting for jobs...")

    while _running:
        job_id = dequeue_job(timeout=5)
        if job_id is None:
            continue
        try:
            run_ingestion(job_id, source=None)
        except Exception:  # noqa: BLE001 - already recorded on the job; keep consuming
            log.exception("Job %s raised; continuing", job_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
