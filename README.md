# Anime Recommender Platform

A retrieval-augmented **anime recommendation platform**, refactored from a single Streamlit
demo into a professional, multi-tier system:

- **Portals** — Angular front-ends (Customer Portal + Admin UI), run natively (`ng serve`).
- **Middleware** — FastAPI microservices (recommender, vectorstore, ingestion), run natively
  (uvicorn). The portals talk to these over HTTP.
- **DevOps/Local** — Dockerized **infrastructure only**: Postgres, Redis, and a full
  observability stack (Prometheus, Loki + promtail, Grafana, Elasticsearch, Kibana, Jaeger).

> Application code is **not** containerized — only infrastructure runs in Docker. Services and
> portals run natively for a fast local dev loop.

## Architecture

```
                 ┌──────────────────────┐      ┌──────────────────────┐
                 │  Portals/             │      │  Portals/            │
                 │  customer-portal      │      │  admin-ui            │
                 │  (Angular :4200)      │      │  (Angular :4300)     │
                 └──────────┬───────────┘      └──────────┬───────────┘
                            │ HTTP                         │ HTTP
                 ┌──────────▼──────────────────────────────▼──────────┐
                 │                  Middleware/ (FastAPI)              │
                 │                                                     │
                 │  recommender-service  :8003   POST /recommend       │
                 │        │  Redis cache + LLM (Groq, LCEL)            │
                 │        ▼                                            │
                 │  vectorstore-service  :8001   /index  /search       │
                 │        │  HF embeddings + Chroma                    │
                 │  ingestion-service    :8002   /ingest /jobs /catalog│
                 │        │  CSV → Postgres + Redis worker → /index    │
                 └──────────┬─────────────┬───────────────┬───────────┘
                            │             │               │
                   ┌────────▼───┐  ┌──────▼─────┐   ┌──────▼─────────────┐
                   │ Postgres   │  │  Redis     │   │ Observability      │
                   │ (catalog,  │  │ (cache +   │   │ Prometheus/Grafana │
                   │  jobs,     │  │  job queue)│   │ Loki/Promtail      │
                   │  users)    │  │            │   │ Elasticsearch/Kibana│
                   └────────────┘  └────────────┘   │ Jaeger (traces)    │
                                                     └────────────────────┘
```

## Repository layout

```
Portals/                 Angular front-ends (native)
  customer-portal/        preference search → recommendations
  admin-ui/               ingestion control, job status, catalog browse, health
Middleware/              FastAPI microservices (native)
  shared/                 config, logging, exceptions, db models, redis, schemas, observability
  recommender-service/    POST /recommend  (Groq + retrieval + Redis cache)
  vectorstore-service/    POST /index, POST /search  (HF embeddings + Chroma)
  ingestion-service/      POST /ingest, GET /jobs/{id}, GET /catalog  (CSV → Postgres + worker)
DevOps/Local/            Dockerized infra (per-component docker-compose.yaml) + orchestration
data/                    seed dataset (anime_with_synopsis.csv, MyAnimeList export)
docs/                    legacy course notes
scripts/                 dev helper scripts invoked by package.json
```

## Quickstart

Prerequisites: Docker, Python 3.12+ (with [uv](https://docs.astral.sh/uv/) or pip), Node 20+.

```bash
# 1. Configure
cp .env.example .env        # fill in GROQ_API_KEY (and HF token if needed)

# 2. Start infrastructure (Docker). Reuses any already-running containers.
npm run infra:up
npm run infra:status

# 3. Install + run the Middleware services natively (uvicorn)
npm run install:services
npm run dev:services        # recommender :8003, vectorstore :8001, ingestion :8002 + worker

# 4. Install + run the Angular Portals natively
npm run install:portals
npm run dev:portals         # customer-portal :4200, admin-ui :4300

# 5. Use it
#    - Admin UI  → trigger ingestion, watch job status, browse catalog
#    - Customer  → enter preferences, get 3 recommendations

# 6. Tear down infra (does NOT stop containers it reused/didn't start)
npm run infra:down
```

### Observability endpoints (after `infra:up`)

| Tool | URL | Purpose |
|---|---|---|
| Grafana | http://localhost:3000 | metrics + logs dashboards |
| Prometheus | http://localhost:9090 | metrics scrape |
| Kibana | http://localhost:5601 | log search (ELK) |
| Jaeger | http://localhost:16686 | distributed traces |

## Notes

- `npm run infra:up` is **idempotent**: for each component it checks whether a container is
  already running (by published port / name) and **reuses** it instead of starting a duplicate.
- Docker images use the versions already present locally where available; see
  `DevOps/Local/*/docker-compose.yaml`.
- Migrated from a Udemy course project; original code preserved under `BackUp/` during the
  refactor and removed once the platform is complete. Legacy K8s deploy notes are in
  `docs/legacy-k8s-deploy.md`.
