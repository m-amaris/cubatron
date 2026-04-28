from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

password_hash = PasswordHash.recommended()

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)

def create_access_token(data: dict, expires_minutes: int | None = None):
    """Create a JWT access token.

    If ``expires_minutes`` is provided it overrides the default from config.
    """
    minutes = ACCESS_TOKEN_EXPIRE_MINUTES if expires_minutes is None else int(expires_minutes)
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
