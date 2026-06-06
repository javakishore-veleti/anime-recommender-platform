# vectorstore-service

FastAPI service owning the vector store: HuggingFace embeddings + persistent Chroma.

| Endpoint | Purpose |
|---|---|
| `POST /index` | upsert documents (`{documents: [{id, text, metadata}]}`) → `{indexed}` |
| `POST /search` | `{query, k}` → `{hits: [{text, score, metadata}]}` |
| `GET /health` | liveness |
| `GET /metrics` | Prometheus metrics |

Run: `npm run dev:vectorstore` (default port `:8001`). The Chroma store persists to
`CHROMA_PERSIST_DIR`. The first index/search call loads the embedding model.
