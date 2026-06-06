#!/usr/bin/env bash
# Start both Angular portals as background daemons (ng serve).
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

start_portal() {
  local name="$1" dir="$2" port="$3" pidfile="$RUN_DIR/$1.pid"
  if pid_alive "$pidfile"; then
    echo "  $name already running (pid $(cat "$pidfile"))"; return
  fi
  if [ ! -d "$REPO_ROOT/Portals/$dir/node_modules" ]; then
    echo "  !! $name deps missing — run: npm run localhost:portals:install-all"
  fi
  ( cd "$REPO_ROOT" && nohup npm --prefix "Portals/$dir" start -- --port "$port" \
      >"$LOG_DIR/$name.out" 2>&1 & echo $! >"$pidfile" )
  echo "  started $name on :$port (pid $(cat "$pidfile"))"
}

echo "==> starting portals"
start_portal customer-portal customer-portal "$CUSTOMER_PORTAL_PORT"
start_portal admin-ui        admin-ui        "$ADMIN_UI_PORT"
echo "==> customer-portal :$CUSTOMER_PORTAL_PORT | admin-ui :$ADMIN_UI_PORT (first compile takes a moment)"
