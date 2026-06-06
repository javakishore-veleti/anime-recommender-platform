#!/usr/bin/env bash
# Stop + remove all infra containers THIS project started.
#
# Safe with the reuse model: `docker compose down` only removes containers that
# the given compose file created. If a component was reused (a pre-existing
# container we skipped at `up`), there is nothing for that compose project to
# remove, so reused/external containers are left untouched.
set -euo pipefail

DEVOPS_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$DEVOPS_DIR/../.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"
NETWORK="anime-net"

ENV_ARG=()
[ -f "$ENV_FILE" ] && ENV_ARG=(--env-file "$ENV_FILE")

KEEP_VOLUMES="${KEEP_VOLUMES:-1}"  # set KEEP_VOLUMES=0 to also drop named volumes
DOWN_ARGS=()
[ "$KEEP_VOLUMES" = "0" ] && DOWN_ARGS=(-v)

for compose in "$DEVOPS_DIR"/*/docker-compose.yaml; do
  name="$(basename "$(dirname "$compose")")"
  echo "==> $name: down"
  docker compose "${ENV_ARG[@]}" -f "$compose" down "${DOWN_ARGS[@]}" || true
done

# Remove the shared network if no longer in use (ignored if still attached).
docker network rm "$NETWORK" >/dev/null 2>&1 || true
echo "==> done."
