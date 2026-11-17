import hashlib
import os
import secrets
import warnings
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "development").strip().lower()
ALGORITHM = "HS256"

try:
    _raw_ttl = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
except ValueError:
    _raw_ttl = 60
ACCESS_TOKEN_EXPIRE_MINUTES = max(5, min(_raw_ttl, 1440))

_configured_secret = os.getenv("SECRET_KEY", "").strip()
if ENVIRONMENT == "production":
    if len(_configured_secret) < 32:
        raise RuntimeError(
            "SECRET_KEY environment variable must be set to at least 32 characters in production."
        )
    SECRET_KEY = _configured_secret
else:
    if len(_configured_secret) < 32:
        warnings.warn(
            "SECRET_KEY env var is missing or shorter than 32 chars; using an ephemeral per-process dev key.",
            RuntimeWarning,
            stacklevel=2,
        )
        SECRET_KEY = secrets.token_urlsafe(48)
    else:
        SECRET_KEY = _configured_secret

password_hasher = PasswordHasher()


def _prehash_password(password: str) -> bytes:
    # Pre-hash with SHA-256 so arbitrarily long passwords stay fixed-length for Argon2
    return hashlib.sha256(password.encode("utf-8")).digest()


def hash_password(password: str) -> str:
    return password_hasher.hash(_prehash_password(password))


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return password_hasher.verify(hashed, _prehash_password(plain))
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": now, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> int:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise credentials_exception

        raw_user_id = payload.get("sub")
        if raw_user_id is None:
            raise credentials_exception

        user_id = int(raw_user_id)
        if user_id <= 0:
            raise credentials_exception
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise credentials_exception

    user = db.get(User, user_id)
    if user is None:
        raise credentials_exception

    return user_id

