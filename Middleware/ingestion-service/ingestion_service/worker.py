"""Background worker: consume ingestion job ids from Redis and run them.

A simple, dependency-free broker (Redis list + BLPOP). Run via
``python -m ingestion_service.worker`` or ``npm run localhost:services:start-all``.
"""

from __future__ import annotations

import signal
import sys
import time

from anime_shared.db import create_all
from anime_shared.logging import get_logger, setup_logging
from anime_shared.redis_client import dequeue_job

from ingestion_service.runner import run_ingestion

log = get_logger("ingestion-service.worker")
_running = True
_BACKOFF_SECONDS = 3


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
        # Guard the dequeue: a blocking-pop timeout or a transient Redis
        # connection blip must NOT kill the worker — log, back off, retry.
        try:
            job_id = dequeue_job(timeout=5)
        except Exception as exc:  # noqa: BLE001 - resilience: keep the worker alive
            log.warning("Redis dequeue failed (%s); retrying in %ss", exc, _BACKOFF_SECONDS)
            time.sleep(_BACKOFF_SECONDS)
            continue
        if job_id is None:
            time.sleep(1)  # idle poll interval (LPOP is non-blocking)
            continue
        try:
            run_ingestion(job_id, source=None)
        except Exception:  # noqa: BLE001 - already recorded on the job; keep consuming
            log.exception("Job %s raised; continuing", job_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
