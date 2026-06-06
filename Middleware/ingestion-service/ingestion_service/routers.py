"""HTTP routes for ingestion-service."""

from __future__ import annotations

from fastapi import APIRouter, Query

from anime_shared.redis_client import enqueue_job
from anime_shared.schemas import CatalogPage, IngestionJobView, IngestRequest

from ingestion_service import catalog, jobs

router = APIRouter(tags=["ingestion"])


@router.post("/ingest", response_model=IngestionJobView, status_code=202)
async def ingest(request: IngestRequest) -> IngestionJobView:
    """Create an ingestion job and enqueue it for the worker."""
    source = request.source_csv or "default-seed-csv"
    job = jobs.create_job(source=source)
    enqueue_job(job.id)
    return job


@router.get("/jobs/{job_id}", response_model=IngestionJobView)
async def get_job(job_id: str) -> IngestionJobView:
    return jobs.get_job(job_id)


@router.get("/catalog", response_model=CatalogPage)
async def get_catalog(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> CatalogPage:
    return catalog.get_catalog_page(limit=limit, offset=offset)
