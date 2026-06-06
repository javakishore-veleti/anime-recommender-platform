#!/usr/bin/env bash
# Run pytest for the shared lib and every Middleware service.
set -euo pipefail
cd "$(dirname "$0")/.."

# shellcheck disable=SC1091
. .venv/bin/activate
for pkg in Middleware/shared Middleware/vectorstore-service Middleware/ingestion-service Middleware/recommender-service; do
  if [ -d "$pkg/tests" ]; then
    echo "==> pytest $pkg"
    ( cd "$pkg" && pytest -q )
  fi
done
echo "==> all tests passed"
