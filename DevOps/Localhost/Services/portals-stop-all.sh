#!/usr/bin/env bash
# Stop both Angular portals.
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

echo "==> stopping portals"
for name in customer-portal admin-ui; do
  stop_pidfile "$name"
done
free_port "$CUSTOMER_PORTAL_PORT"
free_port "$ADMIN_UI_PORT"
echo "==> done."
