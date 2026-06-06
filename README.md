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

## Table of contents

- [Architecture](#architecture)
- [Repository layout](#repository-layout)
- [Quickstart](#quickstart)
- [Run the services](#run-the-services)
- [Run the UI (portals)](#run-the-ui-portals)
- [Container groups & memory](#container-groups--memory)
- [Observability endpoints](#observability-endpoints)
- [Notes](#notes)

## Architecture

```
                 ┌──────────────────────┐      ┌──────────────────────┐
                 │  Portals/             │      │  Portals/            │
                 │  customer-portal      │      │  admin-ui            │
                 │  (Angular :5200)      │      │  (Angular :5201)     │
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

# ...or drive each tier independently (see the sections below).

# 3. Use it
#    - Admin UI  → trigger ingestion, watch job status, browse catalog
#    - Customer  → enter preferences, get 3 recommendations

# 4. Tear down (portals → services → containers)
npm run localhost:stop-all
```

Services + portals run as background daemons (PID files in `.localhost/run/`, logs in
`logs/<name>.out`).

## Run the services

The Middleware FastAPI services (`vectorstore` :8001, `ingestion` :8002, `recommender` :8003)
plus the ingestion worker, run natively via uvicorn.

```bash
npm run localhost:services:install-all   # first time only — creates .venv, installs services
npm run localhost:services:start-all     # start all services + worker (background)
npm run localhost:services:status-all    # PID + /health per service
npm run localhost:services:stop-all      # stop them
npm run localhost:services:restart-all   # stop + start
```

## Run the UI (portals)

The Angular portals — **customer-portal on :5200**, **admin-ui on :5201**.

```bash
npm run localhost:portals:install-all    # first time only — npm install for both portals
npm run localhost:portals:start-all      # ng serve both (background)
npm run localhost:portals:status-all     # PID + HTTP per portal
npm run localhost:portals:stop-all       # stop them
npm run localhost:portals:restart-all    # stop + start
```

Open **http://localhost:5200** (customer) and **http://localhost:5201** (admin).

## Container groups & memory

Docker runs **infrastructure only**, split into groups so a memory-constrained laptop need not
run everything at once:

```bash
npm run localhost:containers:start-all                  # CORE only: Postgres + Redis (default)
npm run localhost:containers:observability:start-all    # OPT-IN heavy stack (ES/Kibana/etc.)
npm run localhost:containers:all:start-all              # everything
npm run localhost:containers:status-all                 # status of all anime-* infra
npm run localhost:containers:stop-all                   # stop all anime-* infra
```

- **`core`** = Postgres + Redis (the default for `containers:start-all`).
- **`observability`** = Prometheus, Loki, Grafana, Elasticsearch, Kibana, Jaeger (opt-in;
  Elasticsearch + Kibana are the memory-heavy ones).
- **Reuse, never duplicate:** start-all checks each component's published port and **reuses** an
  already-running container instead of starting a second one (a Postgres shared with another
  project is not duplicated).
- **Isolated shutdown:** each component runs under a unique `anime-<component>` compose project,
  so stop-all only removes *this* project's containers — other repos' containers (even ones we
  reused on a shared port) are never stopped or restarted.

## Observability endpoints

After `npm run localhost:containers:observability:start-all`:

| Tool | URL | Purpose |
|---|---|---|
| Grafana | http://localhost:3000 | metrics + logs dashboards |
| Prometheus | http://localhost:9090 | metrics scrape |
| Kibana | http://localhost:5601 | log search (ELK) |
| Jaeger | http://localhost:16686 | distributed traces |

## Notes

- Docker images use the versions already present locally where available; see
  `DevOps/Localhost/*/docker-compose.yaml`.
- Migrated from a Udemy course project; original code preserved under `BackUp/` during the
  refactor and removed once the platform is complete. Legacy K8s deploy notes are in
  `docs/legacy-k8s-deploy.md`.
