"""Unit tests for the shared library (no external services required)."""

from __future__ import annotations

from anime_shared.config import Settings
from anime_shared.exceptions import (
    AnimeRecommenderError,
    DownstreamServiceError,
    NotFoundError,
)
from anime_shared.schemas import (
    RecommendationRequest,
    RecommendationResponse,
    SearchHit,
    SearchResponse,
)


def test_settings_defaults_from_env(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_MODEL_NAME", "llama-3.1-8b-instant")
    s = Settings(_env_file=None)
    assert s.groq_api_key == "test-key"
    assert s.embedding_model_name == "all-MiniLM-L6-v2"
    assert s.recommendation_top_k == 5


def test_exception_status_codes_and_chaining():
    assert NotFoundError("x").status_code == 404
    assert DownstreamServiceError("x").status_code == 502
    cause = ValueError("boom")
    err = AnimeRecommenderError("failed", cause=cause)
    assert "boom" in str(err)
    assert err.cause is cause


def test_recommendation_schema_roundtrip():
    req = RecommendationRequest(query="cozy slice of life")
    assert req.query == "cozy slice of life"
    resp = RecommendationResponse(query=req.query, recommendation="1. ...", cached=True)
    assert resp.cached is True
    dumped = resp.model_dump()
    assert dumped["query"] == "cozy slice of life"


def test_search_response_schema():
    resp = SearchResponse(hits=[SearchHit(text="Title: X", score=0.9, metadata={"row": "1"})])
    assert resp.hits[0].score == 0.9
    assert resp.hits[0].metadata["row"] == "1"


def test_recommendation_request_rejects_empty():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        RecommendationRequest(query="")
