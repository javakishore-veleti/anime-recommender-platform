"""Redis access: a shared client plus small cache and job-queue helpers.

Redis serves two roles in the platform:
- **cache**: recommender-service caches LLM responses keyed by query.
- **job queue**: ingestion-service pushes job ids onto a list that the worker
  consumes (a simple, dependency-free broker).
"""

from __future__ import annotations

from functools import lru_cache

import redis

from anime_shared.config import get_settings

INGESTION_QUEUE = "ingestion:jobs"


@lru_cache
def get_redis() -> redis.Redis:
    """Return a process-wide Redis client (decoded responses)."""
    settings = get_settings()
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)


# ---- cache helpers ----------------------------------------------------------

def cache_get(key: str) -> str | None:
    return get_redis().get(key)


def cache_set(key: str, value: str, ttl_seconds: int) -> None:
    get_redis().set(key, value, ex=ttl_seconds)


# ---- job queue helpers ------------------------------------------------------

def enqueue_job(job_id: str, queue: str = INGESTION_QUEUE) -> None:
    get_redis().rpush(queue, job_id)


def dequeue_job(queue: str = INGESTION_QUEUE, timeout: int = 5) -> str | None:
    """Block up to ``timeout`` seconds for the next job id, or return None."""
    result = get_redis().blpop([queue], timeout=timeout)
    if result is None:
        return None
    _, job_id = result
    return job_id
