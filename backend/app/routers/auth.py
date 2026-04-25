"""Admin auth — exchange password for short-lived JWT."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from ..core.auth import create_admin_token, verify_password
from ..schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/admin-token", response_model=TokenResponse)
def admin_token(payload: LoginRequest) -> TokenResponse:
    if not verify_password(payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin password.",
        )
    token, expires_at = create_admin_token()
    return TokenResponse(token=token, expires_at=expires_at)
