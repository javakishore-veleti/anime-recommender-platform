#!/usr/bin/env bash
# Stop + remove infra containers THIS project started.
# Usage: docker-all-down.sh [core|observability|all]   (default: all)
#
# SAFETY: each component is brought down under its OWN unique compose project
# name (anime-<component>), so containers from other repos — even ones we reused
# on a shared port (e.g. a sibling project's Postgres) — are NEVER touched.
# `docker compose down` only removes what its own project created.
set -euo pipefail

DEVOPS_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$DEVOPS_DIR/../.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"
NETWORK="anime-net"
GROUP="${1:-all}"

ENV_ARG=()
if [ -f "$ENV_FILE" ]; then
  set -a; . "$ENV_FILE"; set +a
  ENV_ARG=(--env-file "$ENV_FILE")
fi
# shellcheck source=_components.sh
. "$DEVOPS_DIR/_components.sh"

KEEP_VOLUMES="${KEEP_VOLUMES:-1}"   # KEEP_VOLUMES=0 to also drop named volumes
DOWN_ARGS=()
[ "$KEEP_VOLUMES" = "0" ] && DOWN_ARGS=(-v)

echo "==> stopping containers (group: $GROUP) — only anime-* projects are affected"
for entry in $(select_components "$GROUP"); do
  name="${entry%%:*}"
  compose="$DEVOPS_DIR/$name/docker-compose.yaml"
  [ -f "$compose" ] || continue
  proj="anime-$(printf '%s' "$name" | tr '[:upper:]' '[:lower:]')"
  echo "==> $name: down"
  docker compose -p "$proj" ${ENV_ARG[@]+"${ENV_ARG[@]}"} -f "$compose" down ${DOWN_ARGS[@]+"${DOWN_ARGS[@]}"} || true
done

# Remove the shared network only if nothing else is attached (ignored otherwise).
docker network rm "$NETWORK" >/dev/null 2>&1 || true
echo "==> done."
