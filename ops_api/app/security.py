"""Security helpers for ops API."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable

import jwt
from fastapi import HTTPException, status


class RoleGuard:
    def __init__(self, allowed_roles: Iterable[str]):
        self.allowed_roles = set(allowed_roles)

    def __call__(self, claims: Dict[str, Any]) -> None:
        role = claims.get("role")
        if role not in self.allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")


def create_token(payload: Dict[str, Any], *, expires_delta: timedelta, secret: str) -> str:
    now = datetime.now(timezone.utc)
    data = {**payload, "exp": now + expires_delta, "iat": now, "nbf": now}
    return jwt.encode(data, secret, algorithm="HS256")


def decode_token(token: str, *, secret: str) -> Dict[str, Any]:
    return jwt.decode(token, secret, algorithms=["HS256"])
