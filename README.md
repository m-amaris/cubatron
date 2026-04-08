# Cubatron

Sistema de cocteleria automatizada con interfaz web, API FastAPI y despliegue pensado para Raspberry Pi.

## Estado del proyecto

Este proyecto se ha desarrollado y probado principalmente en:

- Raspberry Pi 3B+
- 1 GB RAM
- Raspberry Pi OS Lite 32-bit (Raspbian)

Eso no impide ejecutarlo en hardware superior, pero la guia y ajustes estan orientados a ese entorno.

## Funcionalidades principales

- Autenticacion de usuarios con JWT.
- Roles `user` y `admin`.
- Perfil de usuario con avatar, tema, acento y datos personales.
- Recetas configurables por admin.
- Configuracion de vasos (CRUD): nombre, icono, capacidad y habilitacion.
- Modos de servido (`low`, `medium`, `high`, `extreme`) con reparto por porcentaje.
- Preparacion con XP variable segun vaso y modo.
- Historial de consumiciones:
  - Global (inicio), paginable y filtrable.
  - Personal (mi perfil), paginable y filtrable.
  - Con avatar, vaso y modo servido.
- Estado de maquina y depositos.
- Ranking global.
- Exposicion local y remota con Tailscale (`tailscale serve`).

## Arquitectura y rutas internas

### Backend

- App FastAPI: `app.main:app`
- Host de escucha: `127.0.0.1`
- Puerto por defecto: `8000`

### Rutas HTTP

- Web:
  - `/` -> login
  - `/dashboard` -> panel principal
  - `/static/...` -> estaticos (avatars, css, js)
- API:
  - `/api/auth/...`
  - `/api/users/...`
  - `/api/drinks/...`
  - `/api/machine/...`
  - `/api/admin/...`
- Salud:
  - `/health`

### Redirecciones/proxy internos

- `cubatron.service` levanta Uvicorn en `127.0.0.1:8000`.
- `cubatron-tailscale-serve.service` publica HTTPS de Tailscale y hace proxy a `http://127.0.0.1:8000`.
- Mapeo Tailscale:
  - `https://<tu-nodo>.ts.net` -> `http://127.0.0.1:8000`

## Estructura de codigo (importante para despliegue)

El despliegue se hace via Git en `/opt/cubatron`. Evita copiar archivos a mano.
Si hay un hotfix manual, respeta este mapeo:

- Local `app/*.py` -> Remoto `/opt/cubatron/app/`
- Local `app/routers/*.py` -> Remoto `/opt/cubatron/app/routers/`

No mezclar archivos de `routers` en la raiz de `app`.

## Requisitos

En Raspberry Pi:

- Python 3.11+ (funciona con 3.13 en pruebas recientes)
- `systemd`
- `curl`
- `openssh-client`/`openssh-server` para despliegue remoto
- (Opcional) Tailscale

Dependencias Python minimas usadas por el proyecto:

- Ver `requirements.txt`.

## Configuracion de entorno

Ejemplo en `.env.example`:

- `CUBATRON_SECRET_KEY`
- `CUBATRON_BOOTSTRAP_ADMIN_USER`
- `CUBATRON_BOOTSTRAP_ADMIN_PASSWORD`
- `CUBATRON_BOOTSTRAP_ADMIN_FULLNAME`

Notas:

- Si no existe `.env`, el script de despliegue puede generarlo automaticamente.
- El seed crea admin inicial solo si no existe ese usuario.
- `app/config.py` fija `BASE_DIR` en `/opt/cubatron`; en local usa ese path o ajusta `BASE_DIR`.

## Inicializacion y arranque

### Desarrollo/local (manual)

```bash
cd /opt/cubatron
python -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

La BD SQLite se crea automaticamente en `/opt/cubatron/data/cubatron.db`.

### Produccion en RPi con systemd + Tailscale (recomendado)

```bash
cd /opt/cubatron
chmod +x scripts/setup_tailscale_vpn.sh
sudo TS_HOSTNAME=cubatron APP_PORT=8000 ./scripts/setup_tailscale_vpn.sh
```

Esto configura:

- `cubatron.service`
- `cubatron-tailscale-serve.service`
- `tailscaled`

## Flujo de trabajo

### Flujo de trabajo local

1) Actualiza el repo y activa tu entorno:

```bash
git pull --ff-only
python -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

2) Arranca el backend en modo local:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

3) Abre la UI:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/dashboard`

La BD SQLite se crea en `data/cubatron.db`.

### Flujo de trabajo en produccion (Raspberry Pi)

1) Servicios activos:

```bash
systemctl status cubatron.service --no-pager
systemctl status cubatron-tailscale-serve.service --no-pager
```

2) Logs recientes:

```bash
journalctl -u cubatron.service -n 100 --no-pager
```

3) Healthcheck local:

```bash
curl -s -o /dev/null -w "health:%{http_code}\n" http://127.0.0.1:8000/health
```

### Preflight antes de desplegar

```bash
ssh miguel@cubatron
cd /opt/cubatron
git status -sb
git fetch
git log --oneline HEAD..origin/main
git diff --stat HEAD..origin/main
systemctl status cubatron.service --no-pager
curl -s -o /dev/null -w "health:%{http_code}\n" http://127.0.0.1:8000/health
```

### Llevar cambios de local a produccion

**En local:**

```bash
git pull --ff-only
git status -sb
git add -A
git commit -m "<mensaje>"
git push origin main
```

**En Raspberry Pi (produccion):**

```bash
ssh miguel@cubatron
cd /opt/cubatron
git status -sb
git pull --ff-only
sudo systemctl restart cubatron.service
```

Verifica que la app quedo arriba:

```bash
systemctl status cubatron.service --no-pager
curl -s -o /dev/null -w "health:%{http_code}\n" http://127.0.0.1:8000/health
```

Notas:

- En produccion no hagas cambios directos: todo debe venir de Git.
- El remoto recomendado es SSH (`git@github.com:m-amaris/cubatron.git`) con deploy key de solo lectura en la RPi.
- Si `git pull --ff-only` falla por divergencia, no hagas merge en produccion:
  - `git fetch`
  - `git log --oneline --left-right HEAD...origin/main`
  - Decide si resetear a `origin/main` o resolver conflictos fuera de prod.
- Si cambian dependencias, ejecuta en la RPi:
  - `. /opt/cubatron/.venv/bin/activate`
  - `pip install -r /opt/cubatron/requirements.txt`

## Modo AP en Raspberry Pi (recomendacion operativa)

Este repo incluye un script rapido para activar/desactivar el perfil AP con NetworkManager.

### Toggle rapido del AP (script)

Script: `scripts/toggle-ap.sh`

Que hace:

- Si la conexion `CubatronAP` esta activa, la baja.
- Si no esta activa, la sube.

Uso:

```bash
cd /opt/cubatron
chmod +x scripts/toggle-ap.sh
./scripts/toggle-ap.sh
```

Requisitos:

- Tener NetworkManager instalado y en uso.
- Tener una conexion llamada exactamente `CubatronAP` (`nmcli connection show`).
- Ejecutar con un usuario que pueda usar `sudo nmcli`.

Si quieres ajustar el nombre de conexion AP, edita el script y cambia `CubatronAP`.

### Configuracion base AP completa (referencia)

Ademas del toggle, esta es una configuracion base recomendada para RPi OS Lite.

### 1) Paquetes

```bash
sudo apt update
sudo apt install -y hostapd dnsmasq avahi-daemon
sudo systemctl unmask hostapd
sudo systemctl enable hostapd dnsmasq avahi-daemon
```

### 2) IP fija para AP (ejemplo)

En `dhcpcd.conf` (interfaz `wlan0`):

```conf
interface wlan0
static ip_address=192.168.50.1/24
nohook wpa_supplicant
```

### 3) hostapd (ejemplo)

`/etc/hostapd/hostapd.conf`:

```conf
country_code=ES
interface=wlan0
ssid=Cubatron-AP
hw_mode=g
channel=6
wmm_enabled=1
auth_algs=1
wpa=2
wpa_passphrase=CambiaEstaClave
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
```

En `/etc/default/hostapd`:

```conf
DAEMON_CONF="/etc/hostapd/hostapd.conf"
```

### 4) dnsmasq (DHCP AP)

`/etc/dnsmasq.d/cubatron-ap.conf`:

```conf
interface=wlan0
dhcp-range=192.168.50.10,192.168.50.200,255.255.255.0,24h
address=/cubatron.local/192.168.50.1
```

### 5) Reinicio servicios

```bash
sudo systemctl restart dhcpcd
sudo systemctl restart hostapd
sudo systemctl restart dnsmasq
```

Con esto, clientes conectados al AP deberian resolver `cubatron.local` hacia la IP local de la Raspberry.

## Acceso local y remoto

- Local (modo AP o cualquier equipo conectado a la misma red de la RPi):
  - `http://cubatron.local`
  - La URL local se resuelve por hostname mDNS de la Raspberry (`cubatron` -> `cubatron.local`).
- Remoto Tailscale:
  - `https://<nodo>.ts.net`

## Verificacion rapida

```bash
systemctl status cubatron.service --no-pager
systemctl status cubatron-tailscale-serve.service --no-pager
tailscale serve status
curl -s -o /dev/null -w "health:%{http_code}\n" http://127.0.0.1:8000/health
```

## Comandos de diagnostico

### Sistema y servicios

```bash
hostnamectl
ip -brief address
sudo systemctl status cubatron.service --no-pager
sudo systemctl status cubatron-tailscale-serve.service --no-pager
sudo systemctl status NetworkManager --no-pager
```

### API local y web

```bash
curl -i http://127.0.0.1:8000/health
curl -I http://127.0.0.1:8000/
curl -I http://127.0.0.1:8000/dashboard
```

### Logs utiles

```bash
sudo journalctl -u cubatron.service -n 200 --no-pager
sudo journalctl -u cubatron-tailscale-serve.service -n 120 --no-pager
sudo journalctl -u NetworkManager -n 120 --no-pager
```

### AP y DNS local

```bash
nmcli connection show --active
nmcli device status
nmcli connection show CubatronAP
grep -R "address=/cubatron.local" /etc/dnsmasq.d /etc/dnsmasq.conf 2>/dev/null
getent hosts cubatron.local
```

### Tailscale

```bash
tailscale status
tailscale serve status
curl -I https://$(hostname).ts.net
```

## Operaciones habituales

### Reiniciar servicio

```bash
sudo systemctl restart cubatron.service
```

### Ver contrasena admin autogenerada

Si el seed ha creado un admin inicial automaticamente, puedes ver el password generado en logs:

```bash
sudo journalctl -u cubatron.service -n 300 --no-pager | grep "Usuario admin inicial creado"
```

### Ver logs

```bash
sudo journalctl -u cubatron.service -n 200 --no-pager
```

### Reaplicar proxy de Tailscale

```bash
sudo systemctl restart cubatron-tailscale-serve.service
tailscale serve status
```

## Despliegue seguro de cambios

Flujo recomendado (Git + systemd):

1. En local: commit y `git push origin main`.
2. En produccion:

```bash
cd /opt/cubatron
git status -sb
git pull --ff-only
sudo systemctl restart cubatron.service
```

3. Verifica `/health` y logs recientes.

Si hay divergencia en prod, no merges: resuelvelo fuera y vuelve a hacer pull.

## Solucion de problemas

### 502 Bad Gateway

Causas tipicas:

- `cubatron.service` caido por error de sintaxis.
- Uvicorn no ha terminado de arrancar.
- Proxy Tailscale apuntando a un backend no disponible.

Acciones:

```bash
sudo systemctl status cubatron.service --no-pager
sudo journalctl -u cubatron.service -n 200 --no-pager
curl -v http://127.0.0.1:8000/health
sudo systemctl restart cubatron-tailscale-serve.service
```

### Dashboard en blanco

Causas tipicas:

- Token caducado/no valido.
- JS desincronizado en servidor.
- Error de API con 401/500.

Acciones:

- Forzar recarga en navegador (Ctrl+F5).
- Cerrar sesion y volver a entrar.
- Revisar logs de `cubatron.service` mientras se carga `/dashboard`.

## Nota sobre Avahi y resolucion local

Configuracion observada en esta Raspberry:

- Hostname del sistema: `cubatron`
- Avahi sin servicios custom en `/etc/avahi/services`
- `publish-workstation=yes` en `/etc/avahi/avahi-daemon.conf`

Con esa configuracion, la resolucion local esperada es por mDNS:

- `cubatron.local`

Esto funciona para clientes en la misma red que soporten mDNS.

### AP de la Raspberry: pasar tambien cubatron.local a clientes AP

El rango DHCP del AP puede variar; lo importante es que los clientes conectados al AP resuelvan `cubatron.local`.

En AP, para garantizarlo incluso en clientes con soporte mDNS irregular, añade una entrada DNS local en `dnsmasq`:

```conf
address=/cubatron.local/192.168.50.1
```

Sustituye `192.168.50.1` por la IP real de `wlan0` en tu AP.

Con eso:

- En AP: `cubatron.local` resuelve por DNS local de `dnsmasq`.
- En LAN normal: `cubatron.local` resuelve por mDNS (Avahi).

## Seguridad recomendada

- Cambiar `CUBATRON_SECRET_KEY` por valor robusto.
- No reutilizar contrasenas por defecto.
- Compartir en Tailscale solo el nodo necesario.
- Mantener sistema y dependencias actualizados.

## Licencia

Define aqui la licencia del proyecto (por ejemplo, MIT) si aplica.
