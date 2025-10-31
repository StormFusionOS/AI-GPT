"""Common FastAPI dependencies for the CRM API."""
from __future__ import annotations

from typing import Dict

from fastapi import Depends, Header, HTTPException, status

from ..core.security import decode_token


async def get_jwt_claims(authorization: str = Header(..., alias="Authorization")) -> Dict[str, str]:
    """Extract and decode a bearer token into JWT claims."""

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    return decode_token(token)
