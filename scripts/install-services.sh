#!/usr/bin/env bash
# Create a single shared virtualenv at repo root and install the shared lib +
# all three Middleware services in editable mode. Used for native local dev.
set -euo pipefail
cd "$(dirname "$0")/.."

PY="${PYTHON:-python3}"
if [ ! -d .venv ]; then
  echo "==> creating .venv"
  "$PY" -m venv .venv
fi
# shellcheck disable=SC1091
. .venv/bin/activate
python -m pip install --upgrade pip

echo "==> installing Middleware/shared + services (editable)"
pip install -e Middleware/shared
pip install -e Middleware/vectorstore-service
pip install -e Middleware/ingestion-service
pip install -e Middleware/recommender-service

echo "==> done. Activate with: source .venv/bin/activate"
