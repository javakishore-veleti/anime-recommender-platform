#!/usr/bin/env bash
# Single source of truth for infra components, their host ports, and groups.
#
# Groups (memory-conscious — this laptop can't run every DB/stack at once):
#   core           -> Postgres, Redis            (required to run the app)
#   observability  -> Prometheus, Loki, Grafana, Elasticsearch, Kibana, Jaeger
#                     (heavy; opt-in. Elasticsearch + Kibana are the big ones.)
#
# Ports honour .env overrides (this file is sourced AFTER .env is loaded).

components_list() {
  cat <<EOF
Postgres:${POSTGRES_PORT:-5433}:core
Redis:${REDIS_PORT:-6379}:core
Prometheus:${PROMETHEUS_PORT:-9090}:observability
Loki:${LOKI_PORT:-3100}:observability
Grafana:${GRAFANA_PORT:-3000}:observability
Elasticsearch:${ELASTICSEARCH_PORT:-9200}:observability
Kibana:${KIBANA_PORT:-5601}:observability
Jaeger:${JAEGER_UI_PORT:-16686}:observability
EOF
}

# select_components <core|observability|all> -> emits "Name:port" lines for the group.
select_components() {
  local want="${1:-core}" line g np
  components_list | while IFS= read -r line; do
    [ -n "$line" ] || continue
    g="${line##*:}"
    np="${line%:*}"
    if [ "$want" = "all" ] || [ "$want" = "$g" ]; then
      echo "$np"
    fi
  done
}

# group_of <ComponentName> -> "core" | "observability"
group_of() {
  components_list | awk -F: -v n="$1" '$1==n {print $3; exit}'
}
