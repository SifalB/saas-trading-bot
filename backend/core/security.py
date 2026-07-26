from datetime import datetime, timedelta, UTC

import bcrypt
from cryptography.fernet import Fernet
from jose import jwt

from .config import settings

try:
    _fernet = Fernet(settings.FERNET_KEY.strip().encode())
except Exception as exc:  # noqa: BLE001 — turn a cryptic traceback into a clear message
    raise RuntimeError(
        "FERNET_KEY is missing or invalid. It must be a 32-byte url-safe "
        "base64 key (44 chars ending in '='). Generate one with: "
        "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
    ) from exc


# ── Passwords ─────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    # bcrypt operates on the first 72 bytes; truncate to stay within that limit.
    pw = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8")[:72], hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(user_id: int) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_token(token: str) -> int:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    return int(payload["sub"])


# ── Binance key encryption ────────────────────────────────────────────────────

def encrypt(value: str) -> str:
    return _fernet.encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    return _fernet.decrypt(value.encode()).decode()
