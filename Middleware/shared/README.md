# anime-shared

Shared cross-cutting library for the anime recommender Middleware services.

| Module | Responsibility |
|---|---|
| `config` | `pydantic-settings` `Settings` + cached `get_settings()` |
| `logging` | structured JSON logging (no global `basicConfig`); optional Elasticsearch shipping |
| `exceptions` | typed `AnimeRecommenderError` hierarchy with HTTP status mapping |
| `models` | SQLAlchemy 2.0 ORM: `AnimeCatalog`, `IngestionJob`, `User`, `SavedRecommendation` |
| `db` | lazy engine/session, `session_scope()`, FastAPI `get_session` dependency |
| `redis_client` | shared client + cache + job-queue helpers |
| `schemas` | shared pydantic DTOs exchanged between services/portals |
| `observability` | Prometheus `/metrics` + OpenTelemetry (Jaeger) tracing |
| `app_factory` | `create_app()` wiring logging, CORS, metrics, tracing, `/health`, error handler |

Installed in editable mode into the shared root venv; each service depends on it.
