#!/usr/bin/env bash
# Bring up local infrastructure (Docker), one per-component compose file.
# Usage: docker-all-up.sh [core|observability|all]   (default: core)
#
# IDEMPOTENT / REUSE: before starting each component, check whether a container
# is ALREADY publishing that component's host port (regardless of which project
# started it). If so, SKIP and reuse it — so we never spin up duplicate DBs.
#
# MEMORY: defaults to the `core` group (Postgres + Redis). The heavy
# observability stack is opt-in via the `observability` (or `all`) argument.
set -euo pipefail

DEVOPS_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$DEVOPS_DIR/../.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"
NETWORK="anime-net"
GROUP="${1:-core}"

# Load .env so component ports honour overrides, and pass it to compose.
ENV_ARG=()
if [ -f "$ENV_FILE" ]; then
  set -a; . "$ENV_FILE"; set +a
  ENV_ARG=(--env-file "$ENV_FILE")
fi
# shellcheck source=_components.sh
. "$DEVOPS_DIR/_components.sh"

mkdir -p "$REPO_ROOT/logs"   # promtail mounts this

if ! docker network inspect "$NETWORK" >/dev/null 2>&1; then
  echo "==> creating docker network: $NETWORK"
  docker network create "$NETWORK" >/dev/null
fi

port_in_use() { docker ps --format '{{.Ports}}' | grep -qE "(^|[^0-9.]):$1->"; }

echo "==> starting containers (group: $GROUP)"
for entry in $(select_components "$GROUP"); do
  name="${entry%%:*}"
  port="${entry##*:}"
  compose="$DEVOPS_DIR/$name/docker-compose.yaml"
  [ -f "$compose" ] || { echo "!! missing $compose, skipping"; continue; }

  if port_in_use "$port"; then
    echo "== $name: port $port already in use — REUSING existing container (skip)"
    continue
  fi
  proj="anime-$(printf '%s' "$name" | tr '[:upper:]' '[:lower:]')"
  echo "==> $name: starting (port $port)"
  docker compose -p "$proj" ${ENV_ARG[@]+"${ENV_ARG[@]}"} -f "$compose" up -d
done

echo "==> done. Status: bash $DEVOPS_DIR/docker-all-status.sh"
