"""Common dependencies for ops API."""
from __future__ import annotations

from typing import Dict

from fastapi import Header, HTTPException

from ..security import decode_token


async def get_claims(authorization: str = Header(..., alias="Authorization")) -> Dict[str, str]:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    return decode_token(token)
