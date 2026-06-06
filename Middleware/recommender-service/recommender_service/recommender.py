"""Recommendation flow: cache -> retrieve -> prompt -> Groq -> cache.

Replaces the original ``src/recommender.py`` + ``pipeline/pipeline.py``. The
deprecated ``RetrievalQA`` chain is gone; retrieval is now an HTTP call to
vectorstore-service and generation is a small LCEL chain (``prompt | llm | parser``).
Responses are cached in Redis keyed by a hash of the (normalized) query.
"""

from __future__ import annotations

import hashlib
from functools import lru_cache

import httpx
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

from anime_shared.config import get_settings
from anime_shared.exceptions import ConfigurationError, DownstreamServiceError
from anime_shared.logging import get_logger
from anime_shared.redis_client import cache_get, cache_set
from anime_shared.schemas import RecommendationResponse, SearchHit

from recommender_service.prompt import get_anime_prompt

log = get_logger("recommender-service.recommender")
_CACHE_PREFIX = "rec:"


def _cache_key(query: str) -> str:
    digest = hashlib.sha256(query.strip().lower().encode("utf-8")).hexdigest()
    return f"{_CACHE_PREFIX}{digest}"


@lru_cache
def _llm() -> ChatGroq:
    settings = get_settings()
    if not settings.groq_api_key:
        raise ConfigurationError("GROQ_API_KEY is not set")
    return ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_model_name,
        temperature=0,
    )


def _retrieve(query: str, k: int) -> list[SearchHit]:
    settings = get_settings()
    url = settings.vectorstore_service_url.rstrip("/") + "/search"
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(url, json={"query": query, "k": k})
            resp.raise_for_status()
            return [SearchHit(**hit) for hit in resp.json().get("hits", [])]
    except httpx.HTTPError as exc:
        raise DownstreamServiceError("vectorstore-service /search failed", cause=exc) from exc


def _build_context(hits: list[SearchHit]) -> str:
    return "\n\n".join(hit.text for hit in hits) if hits else "No relevant anime found."


def recommend(query: str) -> RecommendationResponse:
    """Return recommendations for ``query``, using the Redis cache when possible."""
    settings = get_settings()
    key = _cache_key(query)

    cached = cache_get(key)
    if cached is not None:
        log.info("cache hit for query")
        return RecommendationResponse(query=query, recommendation=cached, cached=True)

    hits = _retrieve(query, settings.recommendation_top_k)
    context = _build_context(hits)

    chain = get_anime_prompt() | _llm() | StrOutputParser()
    try:
        answer = chain.invoke({"context": context, "question": query})
    except Exception as exc:  # noqa: BLE001 - surface LLM failures as downstream errors
        raise DownstreamServiceError("Groq LLM call failed", cause=exc) from exc

    cache_set(key, answer, settings.recommendation_cache_ttl_seconds)
    log.info("recommendation generated and cached")
    return RecommendationResponse(query=query, recommendation=answer, cached=False)
