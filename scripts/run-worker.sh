#!/usr/bin/env bash
# Run the ingestion-service background worker (consumes the Redis job queue).
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -f .env ]; then set -a; . ./.env; set +a; fi

# shellcheck disable=SC1091
. .venv/bin/activate
echo "==> ingestion worker (Redis queue consumer)"
exec python -m ingestion_service.worker
