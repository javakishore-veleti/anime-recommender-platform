#!/usr/bin/env bash
# Start all Python Middleware services + the ingestion worker as background
# daemons (PID files in .localhost/run, logs in logs/<name>.out).
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

if [ ! -d "$VENV" ]; then
  echo "!! venv missing — run: npm run localhost:services:python:install-all"
  exit 1
fi
# shellcheck disable=SC1091
. "$VENV/bin/activate"

start_uvicorn() {
  local name="$1" target="$2" port="$3" pidfile="$RUN_DIR/$1.pid"
  if pid_alive "$pidfile"; then
    echo "  $name already running (pid $(cat "$pidfile"))"; return
  fi
  ( cd "$REPO_ROOT" && nohup uvicorn "$target" --host 0.0.0.0 --port "$port" \
      >"$LOG_DIR/$name.out" 2>&1 & echo $! >"$pidfile" )
  echo "  started $name on :$port (pid $(cat "$pidfile"))"
}

start_worker() {
  local name="ingestion-worker" pidfile="$RUN_DIR/ingestion-worker.pid"
  if pid_alive "$pidfile"; then
    echo "  $name already running (pid $(cat "$pidfile"))"; return
  fi
  ( cd "$REPO_ROOT" && nohup python -m ingestion_service.worker \
      >"$LOG_DIR/$name.out" 2>&1 & echo $! >"$pidfile" )
  echo "  started $name (pid $(cat "$pidfile"))"
}

echo "==> starting python services"
start_uvicorn vectorstore-service vectorstore_service.main:app "$VECTORSTORE_SERVICE_PORT"
start_uvicorn ingestion-service   ingestion_service.main:app   "$INGESTION_SERVICE_PORT"
start_uvicorn recommender-service recommender_service.main:app "$RECOMMENDER_SERVICE_PORT"
start_worker
echo "==> logs in $LOG_DIR/*.out ; status: npm run localhost:services:python:status-all"
