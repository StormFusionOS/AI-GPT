"""Common dependencies for ops API."""
from __future__ import annotations

from typing import Dict, Generator

import jwt
from fastapi import Depends, Header, HTTPException

from ..core.config import get_settings
from ..db import DatabaseSession, get_session
from ..security import RoleGuard, decode_token
from ..services.wordpress import WordPressSite, get_wordpress_site


_OPS_ROLES = RoleGuard(["SEO_ENGINEER", "DEVOPS", "OWNER"])


async def get_claims(authorization: str = Header(..., alias="Authorization")) -> Dict[str, str]:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    settings = get_settings()
    try:
        return decode_token(token, secret=settings.secret_key)
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc


async def require_ops_claims(claims: Dict[str, str] = Depends(get_claims)) -> Dict[str, str]:
    """Ensure only ops-side roles can call protected endpoints."""

    _OPS_ROLES(claims)
    return claims


def get_db() -> Generator[DatabaseSession, None, None]:
    yield from get_session()


def get_wordpress() -> WordPressSite:
    return get_wordpress_site()


__all__ = ["get_claims", "require_ops_claims", "get_db", "get_wordpress"]
