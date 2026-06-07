"""Reusable, importable ingestion pipeline (no third-party data).

These functions are the single source of truth for ingestion and are called by
BOTH the lightweight Redis worker and the Airflow DAGs (reusable → conceptual →
facade). The catalog is generated and written to Postgres in small CHUNKS with a
commit per chunk, so a 100k–1M load never holds a giant transaction or large
memory — it won't choke the machine. Only a small SAMPLE is embedded into the
vector store (embedding millions on CPU is infeasible).
"""

from __future__ import annotations

from collections.abc import Callable

import httpx
from anime_shared.config import get_settings
from anime_shared.db import create_all, get_engine
from anime_shared.exceptions import DownstreamServiceError
from anime_shared.logging import get_logger
from anime_shared.models import AnimeCatalog, JobStatus
from anime_shared.schemas import IndexDocument, IndexRequest
from sqlalchemy import text

from ingestion_service import generator, jobs

log = get_logger("ingestion-service.pipeline")

# Concepts = the genres the catalog is categorized by (one batch each).
CONCEPTS: list[str] = list(generator.GENRES)

_INDEX_BATCH = 256
_COPY_COLUMNS = (
    "title", "synopsis", "genres", "score", "year", "episodes", "studio", "status",
    "combined_info",
)


def _qualified_table() -> str:
    schema = get_settings().db_schema
    name = AnimeCatalog.__tablename__
    return f'"{schema}".{name}' if schema else name


def concept_ranges(count: int, concepts: list[str] | None = None) -> list[tuple[str, int, int]]:
    """Split ``count`` into disjoint, contiguous global-index ranges per concept.

    Contiguous ranges keep generated titles unique across concepts and let each
    conceptual DAG run independently with a fixed (concept, start, n).
    """
    concepts = concepts or CONCEPTS
    base, rem = divmod(count, len(concepts))
    ranges: list[tuple[str, int, int]] = []
    start = 0
    for idx, concept in enumerate(concepts):
        n = base + (1 if idx < rem else 0)
        ranges.append((concept, start, n))
        start += n
    return ranges


def truncate_catalog() -> None:
    with get_engine().begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {_qualified_table()} RESTART IDENTITY"))


def _copy_rows(rows: list[generator.AnimeRow]) -> None:
    """COPY one chunk in its own transaction (gentle on the system)."""
    engine = get_engine()
    cols = ", ".join(_COPY_COLUMNS)
    raw = engine.raw_connection()
    try:
        cur = raw.cursor()
        with cur.copy(f"COPY {_qualified_table()} ({cols}) FROM STDIN") as copy:
            for r in rows:
                copy.write_row(
                    (r.title, r.synopsis, r.genres, r.score, r.year, r.episodes,
                     r.studio, r.status, r.combined_info)
                )
        raw.commit()
    finally:
        raw.close()


def load_concept(
    concept: str,
    start: int,
    n: int,
    seed: int,
    chunk: int | None = None,
    on_chunk: Callable[[int], None] | None = None,
) -> int:
    """Generate + COPY ``n`` anime for one concept, in chunks. Returns rows loaded.

    This is the atomic unit the *reusable* Airflow DAG runs.
    """
    if n <= 0:
        return 0
    chunk = chunk or get_settings().copy_chunk_size
    loaded = 0
    buf: list[generator.AnimeRow] = []
    for i in range(start, start + n):
        buf.append(generator.generate_one(i, seed, primary_genre=concept))
        if len(buf) >= chunk:
            _copy_rows(buf)
            loaded += len(buf)
            if on_chunk:
                on_chunk(len(buf))
            buf = []
    if buf:
        _copy_rows(buf)
        loaded += len(buf)
        if on_chunk:
            on_chunk(len(buf))
    log.info("concept '%s': loaded %d rows", concept, loaded)
    return loaded


def index_sample(sample_size: int, seed: int, count: int | None = None) -> int:
    """Embed a diverse sample (first per-concept slice) into the vector store."""
    settings = get_settings()
    count = count or settings.anime_count
    url = settings.vectorstore_service_url.rstrip("/") + "/index"
    per = max(1, sample_size // len(CONCEPTS))
    docs: list[IndexDocument] = []
    for concept, start, n in concept_ranges(count):
        for i in range(start, start + min(per, n)):
            row = generator.generate_one(i, seed, primary_genre=concept)
            docs.append(IndexDocument(id=str(i), text=row.combined_info, metadata=row.metadata))
            if len(docs) >= sample_size:
                break
        if len(docs) >= sample_size:
            break

    indexed = 0
    try:
        with httpx.Client(timeout=180) as client:
            for off in range(0, len(docs), _INDEX_BATCH):
                payload = IndexRequest(documents=docs[off : off + _INDEX_BATCH])
                resp = client.post(url, json=payload.model_dump())
                resp.raise_for_status()
                indexed += len(payload.documents)
    except httpx.HTTPError as exc:
        raise DownstreamServiceError("vectorstore-service /index failed", cause=exc) from exc
    log.info("indexed %d sample documents", indexed)
    return indexed


def run_full_ingestion(job_id: str, count: int | None = None, seed: int | None = None) -> int:
    """Full ingestion across all concepts (used by the worker and as a fallback).

    The Airflow facade/conceptual/reusable DAGs call the finer-grained functions
    (``truncate_catalog``, ``load_concept``, ``index_sample``) instead.
    """
    settings = get_settings()
    count = count if count is not None else settings.anime_count
    seed = seed if seed is not None else settings.anime_seed
    sample = min(settings.embed_sample_size, count)

    create_all()
    jobs.update_job(job_id, status=JobStatus.RUNNING)
    truncate_catalog()

    total = 0
    for bi, (concept, start, n) in enumerate(concept_ranges(count)):
        if n <= 0:
            continue
        batch_id = jobs.create_batch(job_id, concept, bi)
        jobs.update_batch(batch_id, status=JobStatus.RUNNING)
        try:
            def _progress(delta: int) -> None:
                nonlocal total
                total += delta
                jobs.update_job(job_id, rows_processed=total)

            rows = load_concept(concept, start, n, seed, on_chunk=_progress)
            jobs.update_batch(batch_id, status=JobStatus.COMPLETED, rows=rows)
        except Exception as exc:  # noqa: BLE001 - mark batch failed, then abort job
            jobs.update_batch(batch_id, status=JobStatus.FAILED, error=str(exc))
            raise

    index_sample(sample, seed, count=count)
    jobs.update_job(job_id, status=JobStatus.COMPLETED, rows_processed=total)
    log.info("ingestion job %s done: %d rows across %d concepts", job_id, total, len(CONCEPTS))
    return total
