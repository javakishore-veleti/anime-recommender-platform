# CLAUDE.md — project memory & working agreement

This file is the portable memory for the **anime-recommender-platform**. A fresh Claude Code
session in any clone of this repo auto-loads it. It records what this project is, the
architecture decisions made with the owner, and the current build state.

## What this is

Originally a Udemy course project (a single Streamlit anime recommender by `data-guru0`),
being refactored extensively into a professional, multi-tier microservices platform owned by
**javakishore-veleti**. The original `.git` was removed and its code quarantined under
`BackUp/` (gitignored, deleted once the refactor is complete). Only `data/`, the prompt text,
and core logic were carried forward as reference.

Anime = Japanese-style animation; the app recommends anime titles from a MyAnimeList synopsis
dataset using retrieval + an LLM.

## Architecture (decided with the owner)

- **Portals/** — full-featured **Angular** front-ends, run **natively** (`ng serve`):
  - `customer-portal` (preference search → recommendations)
  - `admin-ui` (ingestion control, job status, catalog browse, health)
- **Middleware/** — **FastAPI microservices**, one per concern, run **natively** (uvicorn),
  **not** containerized. Portals call them over HTTP.
  - `shared/` — installable lib (`anime_shared`): config (pydantic-settings), JSON logging
    (Loki file + ELK), typed exceptions, SQLAlchemy 2.0 models, redis client, schemas,
    observability, `app_factory.create_app()`.
  - `vectorstore-service` (`:8001`) — HF embeddings + Chroma; `POST /index`, `POST /search`.
  - `ingestion-service` (`:8002`) — `POST /ingest`, `GET /jobs/{id}`, `GET /catalog`; CSV →
    Postgres catalog + Redis-queued worker (`python -m ingestion_service.worker`) → vectorstore.
  - `recommender-service` (`:8003`) — `POST /recommend`; Redis cache → vectorstore `/search`
    → LCEL chain (`prompt | ChatGroq | StrOutputParser`).
  - NOTE: each service's package has a **unique name** (`vectorstore_service`,
    `ingestion_service`, `recommender_service`) — NOT `app` — to avoid collisions in the
    shared venv. uvicorn target = `<pkg>.main:app`.
- **DevOps/Local/** — Docker = **infrastructure only**, one per-component `docker-compose.yaml`
  on shared external network `anime-net`: Postgres, Redis, Prometheus, Loki+promtail, Grafana,
  Elasticsearch, Kibana, Jaeger. `docker-all-{run,status,shutdown}.sh` orchestrate them.
- **Root `package.json`** — single entry point: `infra:up/status/down` (Docker),
  `install:services`, `dev:services` (uvicorn + worker), `dev:portals` (ng serve), `lint`, `test`.

## Hard constraints from the owner (do not violate)

1. **Never commit/push to the original author's repo.** This repo has no `origin` to
   data-guru0; commits use identity `javakishore-veleti <javakishore@gmail.com>`. Public repo:
   `anime-recommender-platform` under `javakishore-veleti`.
2. **Docker only for infra** (DB/Redis/observability) — never containerize the app
   services/portals for local dev.
3. **Reuse already-running containers.** `docker-all-run.sh` checks each component's host port
   and skips+reuses if a container is already serving it (applies to ALL stacks, not just
   Postgres). Shutdown only removes what this project started.
4. **Use the Docker image tags already present locally; do not invent new versions.** Present
   locally: postgres:16, prom/prometheus:v2.53.0, grafana/grafana:10.4.2,
   elasticsearch/kibana 8.15.0, jaegertracing/all-in-one:1.62.0. Pulled (not local, owner
   approved): redis:7-alpine, grafana/loki:3.1.0, grafana/promtail:3.1.0.
5. `BackUp/` holds the original code (gitignored). Delete it only when the platform is complete.

## Modernization notes

- Replaced deprecated LangChain `RetrievalQA` with an LCEL chain; `langchain_community.Chroma`
  → `langchain_chroma`; dropped obsolete `Chroma.persist()`.
- Postgres + Redis introduced (the original had neither).
- Observability: Prometheus/Grafana (metrics), Loki+promtail & Elasticsearch/Kibana (logs),
  Jaeger (OTLP traces); services instrumented via `anime_shared`.

## Build status (update as you go)

- [x] Step 0: detach + quarantine to `BackUp/`, fresh git init as owner
- [x] Root scaffolding (.gitignore, .env.example, README, package.json, scripts/)
- [x] `Middleware/shared` (+ tests: 5 passing)
- [x] `vectorstore-service` (ML deps not installed locally yet; tests written)
- [x] `ingestion-service` (tests: 6 passing, incl. real-CSV loader)
- [x] `recommender-service` (tests: 5 passing)
- [x] `DevOps/Local` infra + observability (all 8 compose files validate)
- [x] `Portals/customer-portal` (Angular 21, builds clean) — search + about, Indigo/Teal design system
- [x] `Portals/admin-ui` (Angular 21, builds clean) — dashboard/ingestion/catalog, sidebar layout
- [ ] Finalize: delete `BackUp/` once owner confirms; optional full vectorstore test run (needs ML deps)

## Portals design system

Shared **Indigo & Teal** palette (owner picked it; **no black/grey**): primary `#4f46e5`,
accent `#06b6d4`, deep-indigo text `#1e1b4b`, light surfaces, gradient hero + soft shadows.
Defined in each portal's `src/styles.scss`. Angular 21 standalone + signals + lazy routes.
customer-portal serves on `:4200`, admin-ui on `:4300`.

## Verifying locally

```bash
cp .env.example .env            # set GROQ_API_KEY
npm run infra:up && npm run infra:status
npm run install:services && npm run dev:services
npm run install:portals && npm run dev:portals     # (after portals are built)
```
Python tests: `source .venv/bin/activate && bash scripts/test.sh`.
`vectorstore-service` tests need ML deps (`pip install -e Middleware/vectorstore-service`).
