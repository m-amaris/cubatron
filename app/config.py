from pathlib import Path
import os
import secrets

BASE_DIR = Path("/opt/cubatron")
DATA_DIR = BASE_DIR / "data"

SECRET_KEY = os.getenv("CUBATRON_SECRET_KEY") or secrets.token_urlsafe(64)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12

DATABASE_URL = f"sqlite:///{DATA_DIR / 'cubatron.db'}"
APP_NAME = "Cubatron"
