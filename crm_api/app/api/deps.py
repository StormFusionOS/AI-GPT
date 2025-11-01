"""Common FastAPI dependencies for the CRM API."""
from __future__ import annotations

from typing import Dict

import jwt
from fastapi import Depends, Header, HTTPException, status

from ..core.config import get_settings
from ..core.security import RoleGuard, decode_token


_SALES_ROLES = RoleGuard(["SALES", "SALES_MANAGER", "OWNER"])


async def get_jwt_claims(authorization: str = Header(..., alias="Authorization")) -> Dict[str, str]:
    """Extract and decode a bearer token into JWT claims."""

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    settings = get_settings()
    try:
        return decode_token(token, secret=settings.secret_key)
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc


async def require_sales_claims(claims: Dict[str, str] = Depends(get_jwt_claims)) -> Dict[str, str]:
    """Ensure the caller has a CRM sales-facing role."""

    _SALES_ROLES(claims)
    return claims


__all__ = ["get_jwt_claims", "require_sales_claims"]
