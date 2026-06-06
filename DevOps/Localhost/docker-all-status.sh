#!/usr/bin/env bash
# Show the status of infra components.
# Usage: docker-all-status.sh [core|observability|all]   (default: all)
set -euo pipefail

DEVOPS_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$DEVOPS_DIR/../.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"
GROUP="${1:-all}"

ENV_ARG=()
if [ -f "$ENV_FILE" ]; then
  set -a; . "$ENV_FILE"; set +a
  ENV_ARG=(--env-file "$ENV_FILE")
fi
# shellcheck source=_components.sh
. "$DEVOPS_DIR/_components.sh"

echo "=== anime-* containers ==="
docker ps --filter "name=anime-" \
  --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}' || true

echo
echo "=== per-component (group: $GROUP) ==="
for entry in $(select_components "$GROUP"); do
  name="${entry%%:*}"
  port="${entry##*:}"
  compose="$DEVOPS_DIR/$name/docker-compose.yaml"
  [ -f "$compose" ] || continue
  proj="anime-$(printf '%s' "$name" | tr '[:upper:]' '[:lower:]')"
  if docker ps --format '{{.Ports}}' | grep -qE "(^|[^0-9.]):$port->"; then
    note="port $port in use (ours or reused)"
  else
    note="not running"
  fi
  printf -- "--- %-14s [%s] ---\n" "$name" "$note"
  docker compose -p "$proj" ${ENV_ARG[@]+"${ENV_ARG[@]}"} -f "$compose" ps || true
done
