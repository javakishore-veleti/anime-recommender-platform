# DevOps/Local — infrastructure (Docker)

Docker here runs **infrastructure only**; application services + portals run natively.
Each component is its own per-folder `docker-compose.yaml` on a shared external network
(`anime-net`), orchestrated by the `docker-all-*.sh` scripts (invoked via root `package.json`).

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
npm run infra:up       # bash docker-all-run.sh
npm run infra:status   # bash docker-all-status.sh
npm run infra:down     # bash docker-all-shutdown.sh
```

## Reuse-if-running (idempotent)

`docker-all-run.sh` checks, per component, whether a container is **already publishing that
component's host port** (regardless of which project started it). If so it **skips and reuses**
the running container instead of starting a duplicate — applied uniformly to every stack.
`docker-all-shutdown.sh` only removes containers this project created, so reused/external
containers are never touched.

## How telemetry flows

- **Metrics**: services expose `/metrics`; Prometheus scrapes them via `host.docker.internal`
  (services run on the host). Grafana visualizes (datasource provisioned).
- **Logs**: services write JSON to `logs/<service>.jsonl`; promtail tails that dir → Loki
  (Grafana), and the services also index directly into Elasticsearch (Kibana).
- **Traces**: services export OTLP/HTTP spans to Jaeger (`:4318`).
