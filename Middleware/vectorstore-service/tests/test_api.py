"""API tests for vectorstore-service (store layer mocked — no model download)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from anime_shared.schemas import SearchHit
from vectorstore_service import store
from vectorstore_service.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "vectorstore-service"


def test_index(monkeypatch):
    monkeypatch.setattr(store, "index_documents", lambda docs: len(docs))
    payload = {
        "documents": [
            {"id": "1", "text": "Title: A", "metadata": {"name": "A"}},
            {"id": "2", "text": "Title: B", "metadata": {"name": "B"}},
        ]
    }
    resp = client.post("/index", json=payload)
    assert resp.status_code == 200
    assert resp.json() == {"indexed": 2}


def test_search(monkeypatch):
    monkeypatch.setattr(
        store,
        "search",
        lambda query, k: [SearchHit(text="Title: A", score=0.1, metadata={"name": "A"})],
    )
    resp = client.post("/search", json={"query": "action", "k": 1})
    assert resp.status_code == 200
    hits = resp.json()["hits"]
    assert len(hits) == 1
    assert hits[0]["text"] == "Title: A"
