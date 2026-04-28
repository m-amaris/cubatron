Touch GUI for Cubatron
======================

Minimal framebuffer touchscreen GUI for basic machine control.

Requirements
--
- On Raspberry Pi (Raspbian Lite) with `/dev/fb1` and touchscreen working
- Python packages: `pygame`, `evdev`, `requests` (see `requirements.txt`)
- Run as root or with access to `/dev/input/*` and `/dev/fb1`.

Install (example)
--
1. Install system deps and Python packages:

```bash
sudo apt update
sudo apt install -y python3-pip python3-requests python3-evdev python3-pygame
pip3 install -r requirements.txt
```

2. Create token for a service user (on the Pi or via the web UI) and save it at `/etc/cubatron/touch_token` (one line, the JWT token). The GUI will read this token and use it for authenticated endpoints.

3. Run manually for testing:

```bash
sudo python3 app/touch_gui/gui.py
```

Systemd (example)
--
Create a unit at `/etc/systemd/system/cubatron-touch-gui.service` (see provided template in `deploy/systemd`). Edit paths to match your installation.

Notes and next steps
--
- The current MVP expects an auth token file; it does not implement an on-screen keyboard yet.
- You can extend the GUI: on-screen login, better layout, recipe selection, animations.
