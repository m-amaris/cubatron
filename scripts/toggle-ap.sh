#!/usr/bin/env bash
set -euo pipefail

# Toggle an Access Point using NetworkManager
# Usage: toggle-ap.sh up|down

ACTION=${1:-}
CONN_NAME="Cubatron-AP"
SSID="Cubatron-AP"
PW="cubatron1234"

if [[ "$ACTION" == "up" ]]; then
  nmcli connection add type wifi ifname wlan0 con-name "$CONN_NAME" autoconnect yes ssid "$SSID" >/dev/null 2>&1 || true
  nmcli connection modify "$CONN_NAME" 802-11-wireless.mode ap 802-11-wireless.band bg ipv4.method shared
  nmcli connection modify "$CONN_NAME" wifi-sec.key-mgmt wpa-psk wifi-sec.psk "$PW"
  nmcli connection up "$CONN_NAME"
  echo "AP started"
elif [[ "$ACTION" == "down" ]]; then
  nmcli connection down "$CONN_NAME" || true
  nmcli connection delete "$CONN_NAME" || true
  echo "AP stopped"
else
  echo "Usage: $0 up|down"
  exit 2
fi
