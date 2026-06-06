#!/usr/bin/env bash
# Show status of the Python services + worker (PID alive + /health where applicable).
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

check_http() {
  local name="$1" port="$2" pidfile="$RUN_DIR/$1.pid"
  local proc="down" http="-"
  pid_alive "$pidfile" && proc="up (pid $(cat "$pidfile"))"
  if command -v curl >/dev/null 2>&1; then
    curl -fs "http://localhost:$port/health" >/dev/null 2>&1 && http="healthy" || http="unreachable"
  fi
  printf "  %-22s proc=%-18s /health=%s\n" "$name" "$proc" "$http"
}

check_proc() {
  local name="$1" pidfile="$RUN_DIR/$1.pid"
  local proc="down"
  pid_alive "$pidfile" && proc="up (pid $(cat "$pidfile"))"
  printf "  %-22s proc=%s\n" "$name" "$proc"
}

echo "==> python services status"
check_http vectorstore-service "$VECTORSTORE_SERVICE_PORT"
check_http ingestion-service   "$INGESTION_SERVICE_PORT"
check_http recommender-service "$RECOMMENDER_SERVICE_PORT"
check_proc ingestion-worker
