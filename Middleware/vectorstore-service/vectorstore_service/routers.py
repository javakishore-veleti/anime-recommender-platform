"""HTTP routes for vectorstore-service."""

from __future__ import annotations

from fastapi import APIRouter

from anime_shared.schemas import (
    IndexRequest,
    IndexResponse,
    SearchRequest,
    SearchResponse,
)

from vectorstore_service import store

router = APIRouter(tags=["vectorstore"])


@router.post("/index", response_model=IndexResponse)
async def index(request: IndexRequest) -> IndexResponse:
    count = store.index_documents(request.documents)
    return IndexResponse(indexed=count)


@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    hits = store.search(request.query, request.k)
    return SearchResponse(hits=hits)
