"""Shared pydantic DTOs exchanged between services and portals."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

# ---- vectorstore-service ----------------------------------------------------

class IndexDocument(BaseModel):
    id: str
    text: str
    metadata: dict[str, str] = Field(default_factory=dict)


class IndexRequest(BaseModel):
    documents: list[IndexDocument]


class IndexResponse(BaseModel):
    indexed: int


class SearchRequest(BaseModel):
    query: str
    k: int = 5


class SearchHit(BaseModel):
    text: str
    score: float | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    hits: list[SearchHit]


# ---- recommender-service ----------------------------------------------------

class RecommendationRequest(BaseModel):
    query: str = Field(..., min_length=1, examples=["light hearted anime with school settings"])


class RecommendationResponse(BaseModel):
    query: str
    recommendation: str
    cached: bool = False


# ---- ingestion-service ------------------------------------------------------

class IngestRequest(BaseModel):
    concept: str | None = Field(
        default=None, description="Concept/category ref to ingest; null = all concepts."
    )
    datasets: list[str] = Field(
        default_factory=list, max_length=25,
        description="Optional dataset refs/options (<=25) passed through to the pipeline.",
    )
    anime_count: int | None = Field(
        default=None, description="Optional override for how many anime to generate."
    )


class IngestionJobView(BaseModel):
    id: str
    status: str
    source: str
    rows_processed: int
    error: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class IngestionBatchView(BaseModel):
    """Per-concept batch progress within an ingestion job."""

    concept: str
    batch_index: int
    rows: int
    status: str


class CatalogItem(BaseModel):
    """Compact row for list/browse views."""

    id: int
    title: str
    score: float | None = None
    genres: str | None = None
    year: int | None = None
    studio: str | None = None
    status: str | None = None


class AnimeDetail(BaseModel):
    """Full record for the Anime Card / detail page."""

    id: int
    title: str
    synopsis: str | None = None
    genres: str | None = None
    score: float | None = None
    year: int | None = None
    episodes: int | None = None
    studio: str | None = None
    status: str | None = None


class CatalogPage(BaseModel):
    items: list[CatalogItem]
    total: int
    limit: int
    offset: int


# ---- shared ----------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str = "ok"
    service: str
