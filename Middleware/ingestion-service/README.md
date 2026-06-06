# ingestion-service

FastAPI service + background worker that loads the anime dataset into Postgres and the
vector store.

| Endpoint | Purpose |
|---|---|
| `POST /ingest` | create + enqueue an ingestion job → `202` `IngestionJobView` |
| `GET /jobs/{id}` | job status |
| `GET /catalog?limit&offset` | paged catalog (for Admin UI) |
| `GET /health`, `GET /metrics` | liveness, Prometheus metrics |

**Flow:** `/ingest` records a job in Postgres (`ingestion_jobs`) and pushes its id to a Redis
queue. The **worker** (`python -m app.worker`) consumes the queue, loads/cleans the CSV
(building `combined_info`), full-refreshes the `anime_catalog` table, and calls
`vectorstore-service /index`, updating the job to `completed`/`failed`.

Run API: `npm run dev:ingestion` (`:8002`). Run worker: `npm run dev:ingestion-worker`.
