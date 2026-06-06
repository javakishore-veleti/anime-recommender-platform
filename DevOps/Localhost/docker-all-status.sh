#!/usr/bin/env bash
# Show the status of every infra component (per-component compose ps).
set -euo pipefail

DEVOPS_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$DEVOPS_DIR/../.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"

ENV_ARG=()
[ -f "$ENV_FILE" ] && ENV_ARG=(--env-file "$ENV_FILE")

echo "=== anime-* containers ==="
docker ps --filter "name=anime-" \
  --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}' || true

echo
echo "=== per-component compose ps ==="
for compose in "$DEVOPS_DIR"/*/docker-compose.yaml; do
  name="$(basename "$(dirname "$compose")")"
  proj="anime-$(printf '%s' "$name" | tr '[:upper:]' '[:lower:]')"
  echo "--- $name ---"
  docker compose -p "$proj" ${ENV_ARG[@]+"${ENV_ARG[@]}"} -f "$compose" ps || true
done
