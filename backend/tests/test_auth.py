"""Auth: password verification and JWT issuance."""

from __future__ import annotations

import os

import pytest


def _reload_config(monkeypatch: pytest.MonkeyPatch, **env: str) -> None:
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    import importlib

    import app.core.config as cfg

    importlib.reload(cfg)


def test_verify_password_rejects_when_unset(monkeypatch):
    _reload_config(monkeypatch, BAJA_ADMIN_PASSWORD="")
    from app.core import auth

    assert auth.verify_password("anything") is False


def test_verify_password_constant_time_match(monkeypatch):
    _reload_config(monkeypatch, BAJA_ADMIN_PASSWORD="hunter2")
    from app.core import auth

    assert auth.verify_password("hunter2") is True
    assert auth.verify_password("hunter3") is False
    assert auth.verify_password("") is False


def test_admin_token_roundtrip(monkeypatch):
    _reload_config(
        monkeypatch,
        BAJA_ADMIN_PASSWORD="hunter2",
        BAJA_JWT_SECRET="x" * 64,
    )
    from app.core import auth

    token, expires_at = auth.create_admin_token()
    payload = auth.decode_token(token)
    assert payload["role"] == "admin"
    assert payload["sub"] == "admin"
    assert expires_at is not None


def test_decode_invalid_token_raises(monkeypatch):
    _reload_config(monkeypatch, BAJA_JWT_SECRET="x" * 64)
    from fastapi import HTTPException

    from app.core import auth

    with pytest.raises(HTTPException) as exc:
        auth.decode_token("not-a-real-token")
    assert exc.value.status_code == 401
