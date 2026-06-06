#!/usr/bin/env bash
# Shared helpers for the localhost Services scripts.
# Resolves the repo root, loads .env, and defines PID/log directories.
set -euo pipefail

SERVICES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SERVICES_DIR/../../.." && pwd)"
RUN_DIR="$REPO_ROOT/.localhost/run"
LOG_DIR="$REPO_ROOT/logs"
VENV="$REPO_ROOT/.venv"

mkdir -p "$RUN_DIR" "$LOG_DIR"

# Load .env (exported) if present.
if [ -f "$REPO_ROOT/.env" ]; then set -a; . "$REPO_ROOT/.env"; set +a; fi

# Default ports (overridable via .env).
VECTORSTORE_SERVICE_PORT="${VECTORSTORE_SERVICE_PORT:-8001}"
INGESTION_SERVICE_PORT="${INGESTION_SERVICE_PORT:-8002}"
RECOMMENDER_SERVICE_PORT="${RECOMMENDER_SERVICE_PORT:-8003}"
CUSTOMER_PORTAL_PORT="${CUSTOMER_PORTAL_PORT:-5200}"
ADMIN_UI_PORT="${ADMIN_UI_PORT:-5201}"

# pid_alive <pidfile> -> 0 if the recorded PID is running.
pid_alive() {
  local pidfile="$1"
  [ -f "$pidfile" ] || return 1
  local pid
  pid="$(cat "$pidfile" 2>/dev/null || true)"
  [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null
}

# stop_pidfile <name> -> kill the recorded process tree and remove the pidfile.
stop_pidfile() {
  local name="$1" pidfile="$RUN_DIR/$1.pid"
  if pid_alive "$pidfile"; then
    local pid; pid="$(cat "$pidfile")"
    pkill -P "$pid" 2>/dev/null || true   # children first
    kill "$pid" 2>/dev/null || true
    echo "  stopped $name (pid $pid)"
  else
    echo "  $name not running"
  fi
  rm -f "$pidfile"
}

# free_port <port> -> kill whatever is listening on the TCP port (fallback).
free_port() {
  local pids; pids="$(lsof -ti "tcp:$1" 2>/dev/null || true)"
  [ -n "$pids" ] && kill $pids 2>/dev/null || true
}
