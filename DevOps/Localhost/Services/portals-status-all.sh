#!/usr/bin/env bash
# Show status of the Angular portals (PID alive + HTTP reachability).
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

check_portal() {
  local name="$1" port="$2" pidfile="$RUN_DIR/$1.pid"
  local proc="down" http="-"
  pid_alive "$pidfile" && proc="up (pid $(cat "$pidfile"))"
  if command -v curl >/dev/null 2>&1; then
    curl -fs "http://localhost:$port" >/dev/null 2>&1 && http="serving" || http="unreachable"
  fi
  printf "  %-18s proc=%-18s http=%s\n" "$name" "$proc" "$http"
}

echo "==> portals status"
check_portal customer-portal "$CUSTOMER_PORTAL_PORT"
check_portal admin-ui        "$ADMIN_UI_PORT"
