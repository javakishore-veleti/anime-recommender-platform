# admin-ui (Anime Admin Console)

Angular 21 operator console for the platform. Sidebar layout, Indigo & Teal design system.

- **Dashboard** (`/`) — live service-health checks (all three services' `/health`) + catalog size.
- **Ingestion** (`/ingestion`) — trigger an ingestion job and watch its status update live
  (polls `GET /jobs/{id}` until terminal).
- **Catalog** (`/catalog`) — paged table of the Postgres `anime_catalog`.

Talks to `ingestion-service` (`:8002`) primarily, and pings all services for health.

```bash
npm install
npm start          # ng serve on http://localhost:5201
npm run build      # production build → dist/
```

API base URLs are in `src/environments/`. Requires the Middleware services + Docker infra running.
