#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/opt/cubatron"
APP_PORT="${APP_PORT:-8000}"
TS_HOSTNAME="${TS_HOSTNAME:-cubatron}"
TS_ADVERTISE_EXIT_NODE="${TS_ADVERTISE_EXIT_NODE:-0}"
APP_USER="$(stat -c '%U' "$PROJECT_DIR")"
APP_GROUP="$(stat -c '%G' "$PROJECT_DIR")"
VENV_BIN="$PROJECT_DIR/.venv/bin"
UVICORN_BIN="$VENV_BIN/uvicorn"
ENV_FILE="$PROJECT_DIR/.env"

require_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    echo "Este script requiere privilegios de root."
    echo "Ejecuta: sudo APP_PORT=${APP_PORT} TS_HOSTNAME=${TS_HOSTNAME} $0"
    exit 1
  fi
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

install_tailscale_if_needed() {
  if command_exists tailscale && command_exists tailscaled; then
    echo "Tailscale ya esta instalado."
    return
  fi

  if ! command_exists curl; then
    apt-get update
    apt-get install -y curl
  fi

  curl -fsSL https://tailscale.com/install.sh | sh
}

ensure_env_file() {
  if [[ -f "$ENV_FILE" ]]; then
    return
  fi

  local secret
  secret="$(openssl rand -hex 32)"

  cat > "$ENV_FILE" <<EOF
# Entorno local de Cubatron
CUBATRON_SECRET_KEY=${secret}
# Ajusta estos valores si quieres bootstrap de admin automatico
# CUBATRON_BOOTSTRAP_ADMIN_USER=admin
# CUBATRON_BOOTSTRAP_ADMIN_PASSWORD=cambia-esto
# CUBATRON_BOOTSTRAP_ADMIN_FULLNAME=Administrador
EOF

  chown "$APP_USER:$APP_GROUP" "$ENV_FILE"
  chmod 640 "$ENV_FILE"
}

ensure_uvicorn() {
  if [[ -x "$UVICORN_BIN" ]]; then
    return
  fi

  echo "No existe $UVICORN_BIN"
  echo "Instala dependencias en la venv antes de continuar."
  echo "Ejemplo: cd $PROJECT_DIR && .venv/bin/pip install fastapi uvicorn sqlmodel pyjwt"
  exit 1
}

write_cubatron_service() {
  cat > /etc/systemd/system/cubatron.service <<EOF
[Unit]
Description=Cubatron FastAPI service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${APP_USER}
Group=${APP_GROUP}
WorkingDirectory=${PROJECT_DIR}
EnvironmentFile=-${ENV_FILE}
ExecStart=${UVICORN_BIN} app.main:app --host 127.0.0.1 --port ${APP_PORT}
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
EOF
}

write_tailscale_serve_service() {
  local extra_up_args=""
  if [[ "$TS_ADVERTISE_EXIT_NODE" == "1" ]]; then
    extra_up_args="--advertise-exit-node"
  fi

  cat > /etc/systemd/system/cubatron-tailscale-serve.service <<EOF
[Unit]
Description=Expose Cubatron within Tailscale only
After=tailscaled.service network-online.target cubatron.service
Requires=tailscaled.service cubatron.service
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStartPre=/bin/sh -c 'for i in 1 2 3 4 5 6 7 8 9 10; do /usr/bin/tailscale status >/dev/null 2>&1 && exit 0; sleep 2; done; exit 1'
ExecStart=/usr/bin/tailscale up --ssh --hostname=${TS_HOSTNAME} --accept-dns=true ${extra_up_args}
ExecStart=/usr/bin/tailscale serve --bg --https=443 http://127.0.0.1:${APP_PORT}
ExecStop=/usr/bin/tailscale serve reset

[Install]
WantedBy=multi-user.target
EOF
}

enable_services() {
  systemctl daemon-reload
  systemctl enable --now tailscaled
  systemctl enable --now cubatron.service
  systemctl enable --now cubatron-tailscale-serve.service
}

print_result() {
  local ts_dns
  ts_dns="$(tailscale status --json 2>/dev/null | grep -oE '"DNSName":"[^"]+"' | head -n1 | cut -d '"' -f4 || true)"

  echo
  echo "Configuracion completada."
  echo "URL local (LAN/AP): http://cubatron.local"
  if [[ -n "$ts_dns" ]]; then
    echo "URL remota (Tailscale): https://${ts_dns}"
  else
    echo "URL remota (Tailscale): revisa tu DNSName con 'tailscale status --json'."
  fi
  echo
  echo "Comprobaciones utiles:"
  echo "  systemctl status cubatron.service --no-pager"
  echo "  systemctl status cubatron-tailscale-serve.service --no-pager"
  echo "  tailscale serve status"
}

main() {
  require_root
  install_tailscale_if_needed
  ensure_env_file
  ensure_uvicorn
  write_cubatron_service
  write_tailscale_serve_service
  enable_services
  print_result
}

main "$@"
