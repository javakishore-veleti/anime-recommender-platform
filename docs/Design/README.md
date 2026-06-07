# Design diagrams

`architecture.drawio` — open with [draw.io / diagrams.net](https://app.diagrams.net) (desktop
app, web, or the VS Code "Draw.io Integration" extension). It has **5 tabs** along the bottom:

1. **System Overview** — Portals → Middleware → infra at a glance.
2. **Middleware Services** — the shared lib + 3 FastAPI services and their dependencies.
3. **Ingestion Flow** — `Run ingestion` → Redis queue → worker → Postgres + vector index.
4. **Recommendation Flow** — `POST /recommend`, cache-first → retrieve → Groq.
5. **Infra & Observability** — Docker components, the core/observability groups, namespacing,
   and the `localhost:*` orchestration.

Colours follow the platform palette: indigo = portals, teal = services, violet = shared lib,
green = infra/data, amber = observability, red = external (Groq).
