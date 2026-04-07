# Cubatron: URL local + acceso remoto por nodo compartido de Tailscale

Este proyecto incluye un script idempotente para dejar Cubatron accesible con dos accesos distintos, sin dominio propio:

- URL local para la red privada o el AP de la RPi
- URL remota para acceso desde internet mediante Tailscale compartiendo solo el nodo Cubatron

## Requisitos en la Raspberry Pi

- Debian/Raspberry Pi OS con `systemd`
- Proyecto desplegado en `/opt/cubatron`
- Entorno virtual en `/opt/cubatron/.venv` con `uvicorn` disponible

## Instalacion automatica

Ejecuta en la Raspberry Pi:

```bash
cd /opt/cubatron
chmod +x scripts/setup_tailscale_vpn.sh
sudo TS_HOSTNAME=cubatron APP_PORT=8000 ./scripts/setup_tailscale_vpn.sh
```

Esto hace:

- Instala Tailscale (si no existe)
- Activa `tailscaled`
- Crea `/etc/systemd/system/cubatron.service` (FastAPI en `127.0.0.1:8000`)
- Crea `/etc/systemd/system/cubatron-tailscale-serve.service`
- La unidad incluye una espera previa para evitar el error `unexpected state: NoState` tras reinicio
- Ejecuta `tailscale up` + `tailscale serve --bg --https=443 http://127.0.0.1:8000`
- Deja ambos servicios habilitados en reinicio

## URLs disponibles

URL local:

 `http://cubatron.local`

URL remota:

- `https://cubatron.tail03c569.ts.net`

No se recomienda `.local` para acceso remoto por conflictos con mDNS en algunos clientes.

Para dar acceso a amigos, comparte solo el nodo Cubatron en la consola de Tailscale. Así no ven el resto de tu tailnet.

## Como usarlo

Desde la red local o el AP de la RPi, abre `http://cubatron.local`.

Desde fuera, o con Tailscale conectado y el nodo compartido, abre `https://cubatron.tail03c569.ts.net`.

## Verificaciones

```bash
systemctl status cubatron.service --no-pager
systemctl status cubatron-tailscale-serve.service --no-pager
tailscale serve status
tailscale status
```

Si tras un reinicio ves `No serve config`, recarga y reinicia la unidad:

```bash
sudo systemctl daemon-reload
sudo systemctl restart cubatron-tailscale-serve.service
tailscale serve status
```

## Clientes

Desde movil, portatil u otro dispositivo:

1. En LAN/AP, abrir `http://cubatron.local`
2. Con Tailscale, iniciar sesion en la tailnet y abrir `https://cubatron.tail03c569.ts.net`
3. Si vas a compartir acceso con amigos, comparte solo el nodo Cubatron desde Tailscale.

## Notas

- Si cambias el puerto local de Cubatron, reejecuta el script con `APP_PORT=...`.
- Si quieres anunciar exit node, usa `TS_ADVERTISE_EXIT_NODE=1`.
