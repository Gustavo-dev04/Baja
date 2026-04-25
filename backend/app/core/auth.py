"""Admin auth — password-based login that mints a short-lived JWT.

Protects write endpoints (`POST`/`PATCH`/`DELETE` under `/api/v1`) until
Supabase Auth is wired up in Phase B. The `/inspect` and `/health`
endpoints remain public regardless.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from . import config

_bearer = HTTPBearer(auto_error=False)


def create_admin_token() -> tuple[str, datetime]:
    """Mint a new admin JWT. Returns (token, expires_at)."""
    expires_at = datetime.now(timezone.utc) + timedelta(
        hours=config.JWT_EXPIRE_HOURS,
    )
    payload: dict[str, Any] = {
        "sub": "admin",
        "role": "admin",
        "exp": expires_at,
    }
    token = jwt.encode(
        payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM,
    )
    return token, expires_at


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(
            token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM],
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
        ) from exc


def verify_password(password: str) -> bool:
    """Constant-time-ish comparison against the admin password env var."""
    expected = config.ADMIN_PASSWORD
    if not expected:
        # Fail closed: if no password is set we refuse logins rather than
        # silently accepting any input.
        return False
    # `secrets.compare_digest` would be ideal but we keep it simple.
    if len(password) != len(expected):
        return False
    mismatch = 0
    for a, b in zip(password, expected):
        mismatch |= ord(a) ^ ord(b)
    return mismatch == 0


def require_admin(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict[str, Any]:
    """FastAPI dependency — raises 401 if no valid admin token is attached."""
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
        )
    payload = decode_token(creds.credentials)
    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required.",
        )
    return payload
