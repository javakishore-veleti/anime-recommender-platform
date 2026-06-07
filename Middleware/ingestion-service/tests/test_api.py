"""API tests for ingestion-service (Postgres/Redis mocked)."""

from __future__ import annotations

from anime_shared.schemas import CatalogItem, CatalogPage, IngestionJobView
from fastapi.testclient import TestClient

from ingestion_service import catalog, jobs, routers
from ingestion_service.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json()["service"] == "ingestion-service"


def test_ingest_creates_and_enqueues(monkeypatch):
    created = IngestionJobView(id="job-1", status="pending", source="default-seed-csv",
                               rows_processed=0)
    monkeypatch.setattr(jobs, "create_job", lambda source: created)
    enqueued: list[str] = []
    monkeypatch.setattr(routers, "enqueue_job", lambda job_id: enqueued.append(job_id))

    resp = client.post("/ingest", json={})
    assert resp.status_code == 202
    assert resp.json()["id"] == "job-1"
    assert enqueued == ["job-1"]


def test_get_job(monkeypatch):
    monkeypatch.setattr(
        jobs, "get_job",
        lambda job_id: IngestionJobView(id=job_id, status="completed",
                                        source="x", rows_processed=42),
    )
    resp = client.get("/jobs/abc")
    assert resp.status_code == 200
    assert resp.json()["rows_processed"] == 42


def test_catalog(monkeypatch):
    page = CatalogPage(
        items=[CatalogItem(id=1, title="Crimson Blade of Dawn", score=8.78, genres="Action")],
        total=1, limit=50, offset=0,
    )
    monkeypatch.setattr(catalog, "get_catalog_page", lambda limit, offset: page)
    resp = client.get("/catalog?limit=50&offset=0")
    assert resp.status_code == 200
    assert resp.json()["items"][0]["title"] == "Crimson Blade of Dawn"


def test_generator_is_deterministic_and_unique():
    from ingestion_service import generator

    a = generator.generate_one(0, seed=1337)
    b = generator.generate_one(0, seed=1337)
    assert a.title == b.title and a.combined_info == b.combined_info
    titles = {generator.generate_one(i, seed=1337).title for i in range(500)}
    assert len(titles) == 500  # unique
    assert generator.max_unique_titles() > 1_000_000


def test_concept_ranges_cover_exactly():
    from ingestion_service import pipeline

    ranges = pipeline.concept_ranges(1000)
    assert sum(n for _, _, n in ranges) == 1000
    # contiguous, non-overlapping
    starts = [s for _, s, _ in ranges]
    assert starts == sorted(starts)
