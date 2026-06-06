#!/usr/bin/env bash
# Lint + type-check all Python (shared + services) from the shared venv.
set -euo pipefail
cd "$(dirname "$0")/.."

# shellcheck disable=SC1091
. .venv/bin/activate
echo "==> ruff"
ruff check Middleware
echo "==> mypy"
mypy Middleware/shared/src \
  Middleware/vectorstore-service/vectorstore_service \
  Middleware/ingestion-service/ingestion_service \
  Middleware/recommender-service/recommender_service
echo "==> ok"
