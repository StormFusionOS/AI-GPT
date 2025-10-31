"""Common dependencies for ops API."""
from __future__ import annotations

from typing import Dict, Generator

from fastapi import Header, HTTPException

from ..db import DatabaseSession, get_session
from ..security import decode_token
from ..services.wordpress import WordPressSite, get_wordpress_site


async def get_claims(authorization: str = Header(..., alias="Authorization")) -> Dict[str, str]:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    return decode_token(token)


def get_db() -> Generator[DatabaseSession, None, None]:
    yield from get_session()


def get_wordpress() -> WordPressSite:
    return get_wordpress_site()
