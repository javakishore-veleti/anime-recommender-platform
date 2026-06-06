# Anime Recommender Platform

A retrieval-augmented **anime recommendation platform**, refactored from a single Streamlit
demo into a professional, multi-tier system:

- **Portals** — Angular front-ends (Customer Portal + Admin UI), run natively (`ng serve`).
- **Middleware** — FastAPI microservices (recommender, vectorstore, ingestion), run natively
  (uvicorn). The portals talk to these over HTTP.
- **DevOps/Localhost** — Dockerized **infrastructure only**: Postgres, Redis, and a full
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
DevOps/Localhost/        Dockerized infra (per-component compose) + start/stop/status scripts
  Services/               background daemon scripts for native services + portals
data/                    seed dataset (anime_with_synopsis.csv, MyAnimeList export)
docs/                    legacy course notes
scripts/                 lint + test helpers invoked by package.json
```

## Quickstart

Prerequisites: Docker, Python 3.12+, Node 20+.

All operations run through root `package.json` npm scripts, namespaced
`localhost:<group>:<action>` (groups: `containers`, `services`, `portals`).

```bash
# 1. Configure + one-time install (venv + portal deps)
cp .env.example .env                       # fill in GROQ_API_KEY (and HF token if needed)
npm run localhost:install-all              # python venv + both portals' node_modules

# 2. Bring up everything (containers → services → portals)
npm run localhost:start-all
npm run localhost:status-all               # containers + services + portals health

# ...or drive each tier independently:
npm run localhost:containers:start-all     # Docker infra (reuses already-running containers)
npm run localhost:services:start-all       # FastAPI services + ingestion worker (background)
npm run localhost:portals:start-all        # customer-portal :4200, admin-ui :4300

# 3. Use it
#    - Admin UI  → trigger ingestion, watch job status, browse catalog
#    - Customer  → enter preferences, get 3 recommendations

# 4. Tear down (portals → services → containers)
npm run localhost:stop-all
```

Per-group commands all support `:start-all`, `:stop-all`, `:status-all` (services/portals also
`:restart-all`). Services + portals run as background daemons (PID files in `.localhost/run/`,
logs in `logs/<name>.out`).

### Observability endpoints (after `localhost:containers:start-all`)

| Tool | URL | Purpose |
|---|---|---|
| Grafana | http://localhost:3000 | metrics + logs dashboards |
| Prometheus | http://localhost:9090 | metrics scrape |
| Kibana | http://localhost:5601 | log search (ELK) |
| Jaeger | http://localhost:16686 | distributed traces |

## Notes

- `npm run localhost:containers:start-all` is **idempotent**: for each component it checks
  whether a container is already running (by published port) and **reuses** it instead of
  starting a duplicate.
- Docker images use the versions already present locally where available; see
  `DevOps/Localhost/*/docker-compose.yaml`.
- Migrated from a Udemy course project; original code preserved under `BackUp/` during the
  refactor and removed once the platform is complete. Legacy K8s deploy notes are in
  `docs/legacy-k8s-deploy.md`.
