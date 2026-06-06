#!/usr/bin/env bash
# Bring up all local infrastructure (Docker), one per-component compose file.
#
# IDEMPOTENT / REUSE: before starting each component, we check whether a
# container is ALREADY publishing that component's host port (regardless of
# which project/compose started it). If so, we SKIP and reuse the running
# container instead of starting a duplicate. This applies uniformly to every
# stack (Postgres, Redis, Prometheus, Loki, Grafana, Elasticsearch, Kibana,
# Jaeger) — no per-stack special casing.
set -euo pipefail

DEVOPS_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$DEVOPS_DIR/../.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"
NETWORK="anime-net"

ENV_ARG=()
[ -f "$ENV_FILE" ] && ENV_ARG=(--env-file "$ENV_FILE")

# Repo logs dir must exist before promtail mounts it.
mkdir -p "$REPO_ROOT/logs"

# Shared network for cross-component DNS (e.g. Grafana -> prometheus, Kibana -> elasticsearch).
if ! docker network inspect "$NETWORK" >/dev/null 2>&1; then
  echo "==> creating docker network: $NETWORK"
  docker network create "$NETWORK" >/dev/null
fi

# Is some running container already publishing this host port?
port_in_use() {
  docker ps --format '{{.Ports}}' | grep -qE "(^|[^0-9.]):$1->"
}

# component_dir:primary_host_port  (dependency order: stores -> backends -> UIs)
COMPONENTS="
Postgres:${POSTGRES_PORT:-5432}
Redis:${REDIS_PORT:-6379}
Elasticsearch:${ELASTICSEARCH_PORT:-9200}
Kibana:${KIBANA_PORT:-5601}
Prometheus:${PROMETHEUS_PORT:-9090}
Loki:${LOKI_PORT:-3100}
Grafana:${GRAFANA_PORT:-3000}
Jaeger:${JAEGER_UI_PORT:-16686}
"

for entry in $COMPONENTS; do
  name="${entry%%:*}"
  port="${entry##*:}"
  compose="$DEVOPS_DIR/$name/docker-compose.yaml"
  [ -f "$compose" ] || { echo "!! missing $compose, skipping"; continue; }

  if port_in_use "$port"; then
    echo "== $name: port $port already in use by a running container — REUSING (skip up)"
    continue
  fi
  echo "==> $name: starting (port $port)"
  docker compose "${ENV_ARG[@]}" -f "$compose" up -d
done

echo "==> done. Check with: bash $DEVOPS_DIR/docker-all-status.sh"
