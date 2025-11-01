"""Authentication routes for CRM API."""
from __future__ import annotations

import hashlib

from fastapi import APIRouter, HTTPException, status

from ...core.config import get_settings
from ...core.security import create_token
from ...db import session_scope
from ...models import DB, User, UserRole
from ...schemas.auth import LoginRequest, TokenPair

router = APIRouter(tags=["auth"])


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _hash_password(plain_password) == hashed_password


@router.post("/login", response_model=TokenPair)
def login(data: LoginRequest) -> TokenPair:
    settings = get_settings()
    with session_scope():
        user = DB.users.get(data.email)
        if user is None or not verify_password(data.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        access_token = create_token(
            {"sub": str(user.id), "role": user.role.value},
            expires_delta=settings.access_token_ttl(),
            secret=settings.secret_key,
        )
        refresh_token = create_token(
            {"sub": str(user.id), "role": user.role.value, "scope": "refresh"},
            expires_delta=settings.refresh_token_ttl(),
            secret=settings.secret_key,
        )
        return TokenPair(access_token=access_token, refresh_token=refresh_token)
