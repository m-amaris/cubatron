from pathlib import Path
import os
import secrets


def _env_bool(key: str, default: bool) -> bool:
	raw = os.getenv(key)
	if raw is None:
		return default
	return raw.strip().lower() not in {"0", "false", "no", "off"}

BASE_DIR = Path(os.getenv("CUBATRON_BASE_DIR", "/opt/cubatron"))
DATA_DIR = BASE_DIR / "data"

SECRET_KEY = os.getenv("CUBATRON_SECRET_KEY") or secrets.token_urlsafe(64)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12

DATABASE_URL = f"sqlite:///{DATA_DIR / 'cubatron.db'}"
APP_NAME = "Cubatron"

UART_ENABLED = _env_bool("CUBATRON_UART_ENABLED", True)
UART_DRY_RUN = _env_bool("CUBATRON_UART_DRY_RUN", True)
UART_ENFORCE_TANKS = _env_bool("CUBATRON_UART_ENFORCE_TANKS", True)
UART_PORT = os.getenv("CUBATRON_UART_PORT", "/dev/serial0")
UART_BAUDRATE = int(os.getenv("CUBATRON_UART_BAUDRATE", "115200"))
UART_TIMEOUT = float(os.getenv("CUBATRON_UART_TIMEOUT", "0.5"))
UART_WRITE_TIMEOUT = float(os.getenv("CUBATRON_UART_WRITE_TIMEOUT", "0.5"))
UART_LOG_PATH = os.getenv("CUBATRON_UART_LOG_PATH") or str(DATA_DIR / "uart.log")
