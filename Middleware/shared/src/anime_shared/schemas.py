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
    source_csv: str | None = Field(
        default=None, description="Override the seed CSV path; defaults to the configured dataset."
    )


class IngestionJobView(BaseModel):
    id: str
    status: str
    source: str
    rows_processed: int
    error: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CatalogItem(BaseModel):
    id: int
    mal_id: int | None = None
    name: str
    score: float | None = None
    genres: str | None = None
    synopsis: str | None = None


class CatalogPage(BaseModel):
    items: list[CatalogItem]
    total: int
    limit: int
    offset: int


# ---- shared ----------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str = "ok"
    service: str
