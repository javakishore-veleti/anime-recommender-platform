#!/usr/bin/env bash
# Create the shared venv and install the shared lib + all Python services (editable).
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

PY="${PYTHON:-python3}"
if [ ! -d "$VENV" ]; then
  echo "==> creating venv at $VENV"
  "$PY" -m venv "$VENV"
fi
# shellcheck disable=SC1091
. "$VENV/bin/activate"
python -m pip install --upgrade pip
echo "==> installing shared + services (editable)"
pip install \
  -e "$REPO_ROOT/Middleware/shared" \
  -e "$REPO_ROOT/Middleware/vectorstore-service" \
  -e "$REPO_ROOT/Middleware/ingestion-service" \
  -e "$REPO_ROOT/Middleware/recommender-service"
echo "==> done."
