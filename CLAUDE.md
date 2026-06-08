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
  - `ingestion-service` (`:8002`) — `POST /ingest`, `GET /jobs/{id}`, `GET /catalog`; original
    **synthetic generator** (`generator.py`, no third-party data) → chunked `COPY` into the
    Postgres catalog (one batch per genre/"concept") + a small embedded sample → vectorstore.
    Redis-queued worker (`python -m ingestion_service.worker`); reusable pipeline in
    `pipeline.py` (`truncate_catalog` / `load_concept` / `index_sample` / `run_full_ingestion`).
  - `recommender-service` (`:8003`) — `POST /recommend`; Redis cache → vectorstore `/search`
    → LCEL chain (`prompt | ChatGroq | StrOutputParser`).
  - NOTE: each service's package has a **unique name** (`vectorstore_service`,
    `ingestion_service`, `recommender_service`) — NOT `app` — to avoid collisions in the
    shared venv. uvicorn target = `<pkg>.main:app`.
- **DevOps/Localhost/** — Docker = **infrastructure only**, one per-component `docker-compose.yaml`
  on shared external network `anime-net`: Postgres, Redis, Prometheus, Loki+promtail, Grafana,
  Elasticsearch, Kibana, Jaeger. `docker-all-{up,down,status}.sh` orchestrate them; `Services/`
  holds background daemon scripts for the native services + portals.
- **Root `package.json`** — single entry point, VKP-style `localhost:<group>:<action>` scheme
  (`containers` / `services` / `portals`), each with `start-all`/`stop-all`/`status-all`
  (+`restart-all`), plus top-level `localhost:install-all` / `start-all` / `stop-all` /
  `status-all`. Also `lint`, `test`, `build:portals`.

## Hard constraints from the owner (do not violate)

1. **Never commit/push to the original author's repo.** This repo has no `origin` to
   data-guru0; commits use identity `javakishore-veleti <javakishore@gmail.com>`. Public repo:
   `anime-recommender-platform` under `javakishore-veleti`.
2. **Docker only for infra** (DB/Redis/observability) — never containerize the app
   services/portals for local dev.
3. **Reuse already-running containers; never touch other repos'.** `docker-all-up.sh` checks
   each component's host port and skips+reuses if a container is already serving it (all stacks,
   not just Postgres). Every component runs under a unique `anime-<component>` compose project,
   so `docker-all-down.sh` only removes THIS project's containers — a sibling repo's
   `vkp-postgres` etc. is never stopped/restarted. The laptop is memory-constrained, so infra is
   split into groups: **core** (Postgres+Redis, the default for `containers:start-all`) and
   **observability** (Prometheus/Loki/Grafana/Elasticsearch/Kibana/Jaeger, opt-in via
   `containers:observability:*` or `containers:all:*`). Component→group map: `_components.sh`.
4. **Share infra servers; isolate by namespace (memory-constrained laptop).** Do NOT run
   duplicate servers and do NOT hardcode another project's container (e.g. vkp-postgres).
   Reuse whatever is already on the port; otherwise start ours. Coexist via namespacing, not
   separate servers:
   - **Postgres** (`:5433`): connect to the `postgres` database (create it if missing), keep
     ALL tables in a dedicated **schema** `DB_SCHEMA=anime` (`Base.metadata` schema). Bootstrap
     in `db.create_all()` is race-safe (services start concurrently).
   - **Redis**: every key namespaced under `REDIS_NAMESPACE=anime` (`redis_client._key`).
   - **ELK**: logs go to the `anime-logs` index.
5. **Use the Docker image tags already present locally; do not invent new versions.** Present
   locally: postgres:16, prom/prometheus:v2.53.0, grafana/grafana:10.4.2,
   elasticsearch/kibana 8.15.0, jaegertracing/all-in-one:1.62.0. Pulled (not local, owner
   approved): redis:7-alpine, grafana/loki:3.1.0, grafana/promtail:3.1.0.
6. `BackUp/` is already deleted (original code preserved upstream at data-guru0's repo).

## Modernization notes

- Replaced deprecated LangChain `RetrievalQA` with an LCEL chain; `langchain_community.Chroma`
  → `langchain_chroma`; dropped obsolete `Chroma.persist()`.
- Postgres + Redis introduced (the original had neither).
- **Data source is an original synthetic generator** (`ingestion_service/generator.py`): every
  title/synopsis/field is procedurally generated from authored word banks — NO third-party data
  (the old `data/anime_with_synopsis.csv` MyAnimeList export was deleted). Generation is
  deterministic (`ANIME_SEED`, default 1337) and scalable to ~1M unique titles. Tunables in
  `.env` / shared `config.py`: `ANIME_COUNT` (catalog rows, default 100k), `EMBED_SAMPLE_SIZE`
  (rows embedded for `/recommend`; CPU-bound, default 5k), `COPY_CHUNK_SIZE` (rows per `COPY`
  txn, default 5k). The full catalog is streamed + `COPY`'d to Postgres in chunks (memory-safe
  for 1M); only the sample is embedded into Chroma. Ingestion is concept-batched by genre so
  it can later be driven by Airflow DAGs (reusable → conceptual → facade).
- Observability: Prometheus/Grafana (metrics), Loki+promtail & Elasticsearch/Kibana (logs),
  Jaeger (OTLP traces); services instrumented via `anime_shared`.

## Build status (update as you go)

- [x] Step 0: detach + quarantine to `BackUp/`, fresh git init as owner
- [x] Root scaffolding (.gitignore, .env.example, README, package.json, scripts/)
- [x] `Middleware/shared` (+ tests: 5 passing)
- [x] `vectorstore-service` (ML deps not installed locally yet; tests written)
- [x] `ingestion-service` (tests: 6 passing, incl. real-CSV loader)
- [x] `recommender-service` (tests: 5 passing)
- [x] `DevOps/Localhost` infra + observability (all 8 compose files validate)
- [x] `Portals/customer-portal` (Angular 21, builds clean) — search + about, Indigo/Teal design system
- [x] `Portals/admin-ui` (Angular 21, builds clean) — dashboard/ingestion/catalog, sidebar layout
- [x] Finalize: `BackUp/` deleted; MIT `LICENSE` added; manual CI (GitHub Actions) green
- [x] Full vectorstore test run — ML deps installed (`pip install -e Middleware/vectorstore-service`),
      `vectorstore-service` suite green (3 passed); full suite green via `scripts/test.sh`
      (shared + vectorstore + ingestion 6 + recommender 5).
- [ ] Optional: live end-to-end run (needs Docker daemon running + `GROQ_API_KEY` in `.env`)

## Portals design system

Shared **Indigo & Teal** palette (owner picked it; **no black/grey**): primary `#4f46e5`,
accent `#06b6d4`, deep-indigo text `#1e1b4b`, light surfaces, gradient hero + soft shadows.
Defined in each portal's `src/styles.scss`. Angular 21 standalone + signals + lazy routes.
customer-portal serves on `:5200`, admin-ui on `:5201`.

## Verifying locally

```bash
cp .env.example .env            # set GROQ_API_KEY
npm run localhost:install-all              # venv + portal deps
npm run localhost:start-all                # containers → services → portals
npm run localhost:status-all
```
Python tests: `source .venv/bin/activate && bash scripts/test.sh`.
`vectorstore-service` tests need ML deps (`pip install -e Middleware/vectorstore-service`).
