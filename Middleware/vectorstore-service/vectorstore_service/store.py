"""Vector store wrapper: HuggingFace embeddings + persistent Chroma.

Modernized from the original ``src/vector_store.py``:
- uses ``langchain_chroma.Chroma`` (the old ``langchain_community.vectorstores.Chroma``
  is deprecated) and ``langchain_huggingface.HuggingFaceEmbeddings``;
- drops the obsolete ``db.persist()`` call (Chroma >= 0.4 persists automatically);
- exposes plain index/search operations instead of being coupled to a CSV loader.
"""

from __future__ import annotations

from functools import lru_cache

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from anime_shared.config import get_settings
from anime_shared.logging import get_logger
from anime_shared.schemas import IndexDocument, SearchHit

log = get_logger("vectorstore-service.store")
COLLECTION_NAME = "anime"


@lru_cache
def _embeddings() -> HuggingFaceEmbeddings:
    settings = get_settings()
    log.info("Loading embedding model: %s", settings.embedding_model_name)
    return HuggingFaceEmbeddings(model_name=settings.embedding_model_name)


@lru_cache
def get_store() -> Chroma:
    """Return the process-wide persistent Chroma store (created on first use)."""
    settings = get_settings()
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=_embeddings(),
        persist_directory=settings.chroma_persist_dir,
    )


def index_documents(documents: list[IndexDocument]) -> int:
    """Upsert documents into the vector store. Returns the number indexed."""
    if not documents:
        return 0
    store = get_store()
    store.add_texts(
        texts=[d.text for d in documents],
        metadatas=[d.metadata for d in documents],
        ids=[d.id for d in documents],
    )
    log.info("Indexed %d documents", len(documents))
    return len(documents)


def search(query: str, k: int) -> list[SearchHit]:
    """Return the top-``k`` most similar documents to ``query``."""
    store = get_store()
    results = store.similarity_search_with_score(query, k=k)
    hits: list[SearchHit] = []
    for doc, score in results:
        metadata = {str(key): str(value) for key, value in (doc.metadata or {}).items()}
        hits.append(SearchHit(text=doc.page_content, score=float(score), metadata=metadata))
    return hits
