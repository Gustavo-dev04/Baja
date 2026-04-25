"""Auth schemas (admin password login)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    token: str
    expires_at: datetime
    token_type: str = "bearer"
