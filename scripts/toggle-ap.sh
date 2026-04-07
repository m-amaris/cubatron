#!/usr/bin/env bash
set -euo pipefail

AP_PROFILE="CubatronAP"

if ! command -v nmcli >/dev/null 2>&1; then
    echo "Error: nmcli no esta disponible. Instala/activa NetworkManager." >&2
    exit 1
fi

if nmcli connection show --active | grep -q "${AP_PROFILE}"; then
    sudo nmcli connection down "${AP_PROFILE}"
    echo "Cubatron AP DESACTIVADO (${AP_PROFILE})"
else
    sudo nmcli connection up "${AP_PROFILE}"
    echo "Cubatron AP ACTIVADO (${AP_PROFILE})"
fi
