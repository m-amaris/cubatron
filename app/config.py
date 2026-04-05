from pathlib import Path
import os

BASE_DIR = Path("/opt/cubatron")
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "uploads"

SECRET_KEY = os.getenv("CUBATRON_SECRET_KEY", "cambia-esta-clave-super-larga-en-produccion")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12

DATABASE_URL = f"sqlite:///{DATA_DIR / 'cubatron.db'}"
APP_NAME = "Cubatron"
