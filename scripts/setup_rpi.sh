#!/usr/bin/env bash
set -euo pipefail

# Minimal setup script for Raspberry Pi (Debian/Ubuntu based)
echo "Updating packages..."
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip git network-manager \
  build-essential ca-certificates curl

echo "Creating venv and installing Python deps..."
python3 -m venv /opt/cubatron/venv
source /opt/cubatron/venv/bin/activate
pip install --upgrade pip
pip install -r /opt/cubatron/requirements.txt || true

echo "Installing Tailscale..."
curl -fsSL https://tailscale.com/install.sh | sh || true

echo "Installing systemd services..."
sudo tee /etc/systemd/system/cubatron.service > /dev/null <<'EOF'
[Unit]
Description=Cubatron FastAPI service
After=network.target

[Service]
User=root
WorkingDirectory=/opt/cubatron
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/cubatron/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/cubatron-tailscale-serve.service > /dev/null <<'EOF'
[Unit]
Description=Cubatron Tailscale serve helper
After=network.target tailscaled.service

[Service]
Type=oneshot
ExecStart=/usr/bin/tailscale up --accept-routes || true

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
echo "Setup complete. Enable services with: sudo systemctl enable --now cubatron.service cubatron-tailscale-serve.service"
