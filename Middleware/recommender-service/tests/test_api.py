"""Tests for recommender-service (LLM, retrieval, and Redis mocked)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from anime_shared.schemas import RecommendationResponse, SearchHit
from recommender_service import recommender
from recommender_service.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json()["service"] == "recommender-service"


def test_recommend_endpoint(monkeypatch):
    monkeypatch.setattr(
        recommender,
        "recommend",
        lambda query: RecommendationResponse(query=query, recommendation="1. Naruto...",
                                             cached=False),
    )
    resp = client.post("/recommend", json={"query": "ninja action"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["recommendation"].startswith("1.")
    assert body["cached"] is False


def test_recommend_rejects_empty_query():
    resp = client.post("/recommend", json={"query": ""})
    assert resp.status_code == 422


def test_cache_hit_short_circuits(monkeypatch):
    """A cache hit must not touch retrieval or the LLM."""
    monkeypatch.setattr(recommender, "cache_get", lambda key: "cached answer")

    def _boom(*_a, **_k):  # pragma: no cover - must never be called on a cache hit
        raise AssertionError("should not be called on cache hit")

    monkeypatch.setattr(recommender, "_retrieve", _boom)
    monkeypatch.setattr(recommender, "_llm", _boom)

    result = recommender.recommend("cozy slice of life")
    assert result.cached is True
    assert result.recommendation == "cached answer"


def test_build_context_handles_empty():
    assert recommender._build_context([]) == "No relevant anime found."
    hits = [SearchHit(text="Title: A"), SearchHit(text="Title: B")]
    assert "Title: A" in recommender._build_context(hits)
