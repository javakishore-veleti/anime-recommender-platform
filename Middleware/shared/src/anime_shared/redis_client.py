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
    """Pop the next job id (non-blocking), or return None if the queue is empty.

    Uses LPOP polling rather than BLPOP: some redis-py versions race the
    blocking-pop's server-side timeout against the client socket read timeout
    and raise ``TimeoutError`` on an idle queue. The caller polls on a short
    sleep instead (see the worker loop). ``timeout`` is accepted for API
    compatibility but unused.
    """
    return get_redis().lpop(queue)
