# DevOps/Localhost — local operations

Docker here runs **infrastructure only**; application services + portals run natively as
background daemons. Each infra component is its own per-folder `docker-compose.yaml` on a
shared external network (`anime-net`), orchestrated by `docker-all-*.sh`. The `Services/`
subfolder holds the daemon scripts for the native Python services and Angular portals. All of
it is driven by the root `package.json` `localhost:*` scripts.

| Component | Image (local tag) | Port | Role |
|---|---|---|---|
| Postgres | `postgres:16` | 5432 | catalog, jobs, users |
| Redis | `redis:7-alpine` | 6379 | rec cache + ingestion broker |
| Prometheus | `prom/prometheus:v2.53.0` | 9090 | metrics scrape |
| Loki + promtail | `grafana/loki:3.1.0`, `grafana/promtail:3.1.0` | 3100 | log aggregation |
| Grafana | `grafana/grafana:10.4.2` | 3000 | metrics + logs dashboards |
| Elasticsearch | `…/elasticsearch:8.15.0` | 9200 | ELK log store |
| Kibana | `…/kibana:8.15.0` | 5601 | log search UI |
| Jaeger | `jaegertracing/all-in-one:1.62.0` | 16686 / 4317 / 4318 | tracing (OTLP) |

## Commands (from repo root)

```bash
# containers — CORE only (Postgres + Redis); memory-friendly default
npm run localhost:containers:start-all
npm run localhost:containers:status-all
npm run localhost:containers:stop-all      # stops ALL anime-* containers (core + observability)

# observability stack (Prometheus/Loki/Grafana/Elasticsearch/Kibana/Jaeger) — opt-in
npm run localhost:containers:observability:start-all
npm run localhost:containers:observability:stop-all

# absolutely everything
npm run localhost:containers:all:start-all

# whole platform (containers → services → portals, reverse on stop)
npm run localhost:start-all
npm run localhost:status-all
npm run localhost:stop-all
```

The scripts take a group argument directly too: `bash docker-all-up.sh [core|observability|all]`
(up defaults to `core`; down/status default to `all`). Components and their groups live in
`_components.sh`.

### Memory & isolation

- **Reuse:** `docker-all-up.sh` skips any component whose host port is already taken and reuses
  the running container — so a Postgres shared with another project is never duplicated.
- **Isolation:** every component runs under a unique `anime-<component>` compose project, so
  `docker-all-down.sh` only ever removes *this* project's containers. Other repos' containers
  (e.g. `vkp-postgres`) are never stopped or restarted.

## Reuse-if-running (idempotent)

`docker-all-up.sh` checks, per component, whether a container is **already publishing that
component's host port** (regardless of which project started it). If so it **skips and reuses**
the running container instead of starting a duplicate — applied uniformly to every stack.
`docker-all-down.sh` only removes containers this project created, so reused/external
containers are never touched.

## How telemetry flows

- **Metrics**: services expose `/metrics`; Prometheus scrapes them via `host.docker.internal`
  (services run on the host). Grafana visualizes (datasource provisioned).
- **Logs**: services write JSON to `logs/<service>.jsonl`; promtail tails that dir → Loki
  (Grafana), and the services also index directly into Elasticsearch (Kibana).
- **Traces**: services export OTLP/HTTP spans to Jaeger (`:4318`).
