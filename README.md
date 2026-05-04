# Cubatron - Guía de Implementación

Sistema de coctelería automatizada con interfaz web, API y control de hardware STM32. Esta guía detalla los pasos para desplegar el proyecto desde cero tanto en entornos de desarrollo local (WSL) como en producción (Raspberry Pi).

## Stack Tecnológico y Arquitectura
- **Frontend:** React, Vite y Tailwind CSS.
- **Backend:** FastAPI (Python) y SQLite (Base de datos local).
- **Hardware:** STM32 conectado por UART a la Raspberry Pi [file:1].

### Estructura Principal del Proyecto
```text
cubatron/
├── app/               # Backend en FastAPI (routers, auth, comunicaciones UART)
├── frontend/          # Código fuente de la interfaz en React/Vite
├── scripts/           # Scripts de sistema para RPi (setup_rpi.sh, tailscale, etc.)
├── data/              # Directorio generado en runtime (cubatron.db, uart.log)
├── requirements.txt   # Dependencias de Python
└── .env.example       # Plantilla de variables de entorno
```

---

## 1. Requisitos Previos

Asegúrate de tener instalados los siguientes componentes en tu sistema (WSL o Raspberry Pi):

- **Python 3.11** (la versión 3.12+ no es compatible con las dependencias actuales).
- **Node.js (v18 o superior)** y `npm` (para el entorno frontend).
- **Git**, **curl** y herramientas básicas de sistema.

### Instalación de Python 3.11

Si tu sistema no tiene Python 3.11 (ej. Debian trixie con Python 3.13), instálalo usando `pyenv`:

```bash
# Instalar dependencias de desarrollo (necesario para compilar Python)
sudo apt update
sudo apt install -y build-essential libssl-dev zlib1g-dev libbz2-dev \
  libreadline-dev libsqlite3-dev wget curl llvm libncursesw5-dev \
  xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

# Instalar pyenv
curl https://pyenv.run | bash

# Configurar pyenv en tu shell (añade al ~/.bashrc para persistencia)
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# Instalar Python 3.11.12
pyenv install 3.11.12
pyenv global 3.11.12
```

Si tu sistema ya tiene Python 3.11 disponible, instala las herramientas básicas:

```bash
sudo apt update
sudo apt install -y python3.11-venv python3-pip git curl nodejs npm
```

## 2. Clonado y Preparación

El sistema está diseñado para ejecutarse de forma agnóstica sin depender de una ruta estricta.

```bash
# 1. Clonar el repositorio
git clone git@github.com:m-amaris/cubatron.git
cd cubatron

# 2. Preparar Backend (Python)
# Si usas pyenv, asegúrate de tener la versión correcta:
# export PYENV_ROOT="$HOME/.pyenv"
# export PATH="$PYENV_ROOT/bin:$PATH"
# eval "$(pyenv init -)"
# pyenv local 3.11.12

python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

# Arreglar compatibilidad de bcrypt (requerido)
pip install bcrypt==4.0.1

# 3. Preparar Frontend (Node.js)
cd frontend
npm install
cd ..
```

## 3. Configuración del Entorno y Base de Datos

Copia el archivo de ejemplo para configurar las variables de entorno de la aplicación:

```bash
cp .env.example .env
nano .env
```
Asegúrate de definir al menos:
- `CUBATRON_SECRET_KEY`: Una cadena segura, única y aleatoria para firmar los tokens JWT. Puedes generar una fácilmente ejecutando este comando en tu terminal y copiando el resultado:
  ```bash
  openssl rand -hex 32
  ```

**Inicialización de la Base de Datos:**
No es necesario ejecutar scripts de migración manuales. La base de datos SQLite (`data/cubatron.db`) se creará automáticamente la primera vez que se inicie la aplicación mediante FastAPI. Además, si el sistema no detecta ningún administrador, **creará automáticamente un usuario por defecto** con las siguientes credenciales:
- **Usuario:** `admin`
- **Contraseña:** `admin`

*(Nota: Se recomienda encarecidamente cambiar esta contraseña desde el Panel de Administración o Mi Perfil tras el primer inicio de sesión).*

## 4. Desarrollo Local (WSL en Windows)

Para desarrollar en local, el flujo de trabajo requiere levantar el backend y el frontend por separado en dos terminales distintas.

**Terminal 1: Backend (FastAPI)**
```bash
# Si usas pyenv, configúralo primero:
# export PYENV_ROOT="$HOME/.pyenv"
# export PATH="$PYENV_ROOT/bin:$PATH"
# eval "$(pyenv init -)"

source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
*Tip: FastAPI genera documentación interactiva automáticamente. Puedes probar la API accediendo a `http://localhost:8000/docs` (Swagger UI) o `/redoc`.*

**Terminal 2: Frontend (Vite)**
```bash
cd frontend
npm run dev
```
*(El frontend de Vite habitualmente se levanta en el puerto `5173` y se configura para hacer proxy de las peticiones `/api` al puerto `8000` de FastAPI).* Desde otros dispositivos se puede acceder a la interfaz accediendo a `http://{IP_EQUIPO}:5173`

### Exponer WSL a la red local (Opcional)
Para probar Cubatron desde otro dispositivo (ej. tu móvil), enruta el puerto de Windows hacia la subred virtual de WSL. En **PowerShell como Administrador**:

1. Obtén la IP de WSL ejecutando `hostname -I` en Linux (ej. `172.21.71.220`).
2. Enruta el puerto:
```powershell
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=172.21.71.220
```
3. Abre el firewall de Windows:
```powershell
netsh advfirewall firewall add rule name="WSL 8000" dir=in action=allow protocol=TCP localport=8000
```
Se puede aplicar el mismo proceso para habilitar acceder al frontend.

## 5. Hardware: Conexiones y UART (STM32)

Cubatron se comunica enviando tramas de texto plano (ej. `|MAKE;20;15;0;0|`) [file:1]. 

**Conexionado Físico (Raspberry Pi -> STM32):**
| Raspberry Pi (Header) | Pin RPi | Función | STM32 |
|-----------------------|---------|---------|-------|
| GPIO 14 (TXD)         | Pin 8   | TX      | **RX**|
| GPIO 15 (RXD)         | Pin 10  | RX      | **TX**|
| Ground                | Pin 6   | GND     | **GND**|

*Aviso: Es vital cruzar TX con RX y compartir el pin de GND (tierra) para que la comunicación serie funcione.*

### Habilitar UART en Raspberry Pi OS (¡Muy Importante!)
Por defecto, la RPi usa el puerto serie para la consola de login. Debes desactivar la consola pero dejar habilitado el puerto físico:
1. Ejecuta `sudo raspi-config`.
2. Ve a **3 Interface Options** -> **I5 Serial Port**.
3. *Would you like a login shell to be accessible over serial?* -> **NO**.
4. *Would you like the serial port hardware to be enabled?* -> **YES**.
5. Reinicia la Raspberry Pi.

**Configuración UART en el `.env`:**
- **Local/WSL:** Mantén `CUBATRON_UART_DRY_RUN=1`. Simularemos la máquina y los comandos se escribirán en `data/uart.log` [file:1].
- **Producción (RPi):** Configura `CUBATRON_UART_PORT=/dev/serial0`, baudrate en `115200` y establece `CUBATRON_UART_DRY_RUN=0` para activar el envío físico [file:1].

## 6. Despliegue en Producción (Raspberry Pi)

En producción, el frontend se compila como archivos estáticos y FastAPI se encarga de servirlos junto con la API.

```bash
# 1. Compilar el frontend (genera la carpeta dist/ que servirá FastAPI)
cd frontend
npm run build
cd ..
```

**Automatización de Servicios:**
El script de configuración se encarga de establecer el **hostname** (`cubatron`), configurar la red en modo **Dual WAN** (red local conocida + Access Point asilado), integrar **Tailscale**, y crear el servicio de **systemd** para la auto-ejecución.

```bash
chmod +x scripts/setup_rpi.sh
sudo ./scripts/setup_rpi.sh
```

El servicio `cubatron.service` levantará FastAPI en `0.0.0.0:8000`.

## 7. Accesibilidad del Sistema

En producción, accede a la interfaz a través de las siguientes vías:
- **Red Local / IP:** `http://<IP_RPI>:8000`
- **Hostname (mDNS):** `http://cubatron:8000`
- **Acceso Remoto:** `https://cubatron.ts.net` (Si tienes Tailscale habilitado).

## 8. Mantenimiento y Operaciones

No modifiques código directamente en la Raspberry Pi.

1. Desarrolla y prueba en WSL.
2. Sube los cambios: `git commit` y `git push`.
3. En la Raspberry Pi, descarga y reinicia:

```bash
git pull --ff-only
# Si hay cambios en el frontend, no olvides compilar: cd frontend && npm run build
sudo systemctl restart cubatron.service
```

### Copias de Seguridad (Backups)
Toda la configuración del sistema (usuarios, historial, configuración de vasos y recetas) se guarda en un único archivo SQLite. Para hacer un backup completo, simplemente copia ese archivo:
```bash
cp data/cubatron.db ~/backup_cubatron_$(date +%F).db
```

### Comandos útiles
- **Estado del servicio:** `systemctl status cubatron.service --no-pager`
- **Ver logs del backend:** `sudo journalctl -u cubatron.service -n 100 --no-pager`
- **Ver actividad UART:** `tail -n 50 -f data/uart.log` [file:1]
- **Probar salud de la API:** `curl -i http://127.0.0.1:8000/health` [file:1]


### Gestión de Concurrencia (Prevención de colisiones)
El sistema está diseñado para ser usado por múltiples usuarios simultáneamente (ej. en una fiesta). Para evitar que la máquina intente preparar dos bebidas a la vez y se saturen las bombas:
- El backend implementa un **bloqueo de estado** en memoria o base de datos (`idle` vs `busy`).
- Si la máquina está `busy` (preparando o limpiando) y un segundo usuario envía una petición a `/api/drinks/make`, la API rechazará la petición inmediatamente con un error HTTP `409 Conflict` (ej. "La máquina está ocupada").
- El estado se sincroniza consultando periódicamente al STM32 mediante el comando UART `STATUS`.