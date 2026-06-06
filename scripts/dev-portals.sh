#!/usr/bin/env bash
# Run both Angular portals natively (ng serve). Ctrl-C stops them all.
set -euo pipefail
cd "$(dirname "$0")/.."

pids=()
cleanup() {
  echo
  echo "==> stopping portals..."
  for pid in "${pids[@]}"; do kill "$pid" 2>/dev/null || true; done
  wait 2>/dev/null || true
}
trap cleanup INT TERM EXIT

npm --prefix Portals/customer-portal start & pids+=($!)
npm --prefix Portals/admin-ui start & pids+=($!)

echo "==> customer-portal :4200 | admin-ui :4300"
echo "==> Ctrl-C to stop all"
wait
