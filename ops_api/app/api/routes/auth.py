"""Authentication endpoints for ops API."""
from __future__ import annotations

from datetime import timedelta

import hashlib

from fastapi import APIRouter, HTTPException, status

from ...core.config import get_settings
from ...security import create_token

router = APIRouter(tags=["auth"])

_fake_users = {
    "ops@example.com": {
        "password": hashlib.sha256("password123".encode("utf-8")).hexdigest(),
        "role": "SEO_ENGINEER",
    }
}


@router.post("/login")
def login(email: str, password: str) -> dict[str, str]:
    record = _fake_users.get(email)
    hashed = hashlib.sha256(password.encode("utf-8")).hexdigest()
    if not record or record["password"] != hashed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    settings = get_settings()
    access = create_token({"sub": email, "role": record["role"]}, expires_delta=timedelta(minutes=settings.access_token_expire_minutes))
    refresh = create_token({"sub": email, "role": record["role"], "scope": "refresh"}, expires_delta=timedelta(minutes=settings.refresh_token_expire_minutes))
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}
