#!/usr/bin/env bash
# Run all Middleware services + the ingestion worker natively, together.
# Ctrl-C stops them all.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -f .env ]; then set -a; . ./.env; set +a; fi

VS_PORT="${VECTORSTORE_SERVICE_PORT:-8001}"
IN_PORT="${INGESTION_SERVICE_PORT:-8002}"
RE_PORT="${RECOMMENDER_SERVICE_PORT:-8003}"

pids=()
cleanup() {
  echo
  echo "==> stopping services..."
  for pid in "${pids[@]}"; do kill "$pid" 2>/dev/null || true; done
  wait 2>/dev/null || true
}
trap cleanup INT TERM EXIT

bash scripts/run-service.sh vectorstore_service.main:app "$VS_PORT" & pids+=($!)
bash scripts/run-service.sh ingestion_service.main:app  "$IN_PORT" & pids+=($!)
bash scripts/run-service.sh recommender_service.main:app "$RE_PORT" & pids+=($!)
bash scripts/run-worker.sh & pids+=($!)

echo "==> vectorstore :$VS_PORT | ingestion :$IN_PORT | recommender :$RE_PORT | + worker"
echo "==> Ctrl-C to stop all"
wait
