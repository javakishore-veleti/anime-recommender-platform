#!/usr/bin/env bash
# Run a single Middleware service via uvicorn from the shared venv.
# Usage: run-service.sh <import-path:app> <port>
#   e.g. run-service.sh vectorstore_service.main:app 8001
# Runs from the repo root so data/ and logs/ paths resolve consistently.
set -euo pipefail
cd "$(dirname "$0")/.."

TARGET="${1:?usage: run-service.sh <module:app> <port>}"
PORT="${2:?usage: run-service.sh <module:app> <port>}"

# Load .env if present (exported for the service process).
if [ -f .env ]; then set -a; . ./.env; set +a; fi

# shellcheck disable=SC1091
. .venv/bin/activate
echo "==> ${TARGET} on :${PORT}"
exec uvicorn "${TARGET}" --reload --host 0.0.0.0 --port "${PORT}"
