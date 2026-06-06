#!/usr/bin/env bash
# Stop all Python services + worker started by python-start-all.sh.
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

echo "==> stopping python services"
for name in vectorstore-service ingestion-service recommender-service ingestion-worker; do
  stop_pidfile "$name"
done
# Port fallback in case a PID file was lost.
free_port "$VECTORSTORE_SERVICE_PORT"
free_port "$INGESTION_SERVICE_PORT"
free_port "$RECOMMENDER_SERVICE_PORT"
echo "==> done."
