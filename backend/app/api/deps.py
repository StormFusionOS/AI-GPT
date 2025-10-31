from dataclasses import dataclass
from typing import Generator

from fastapi import Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db


@dataclass(slots=True)
class ClientContext:
    """Represents the authenticated client derived from request headers."""

    client_id: str
    role: str


def get_db_session() -> Generator[Session, None, None]:
    yield from get_db()


async def require_admin_role(x_user_role: str | None = Header(default=None)) -> None:
    """Simple header-based guard until full authentication is wired."""

    if x_user_role is None or x_user_role.lower() != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Admin privileges required')


async def get_client_context(
    x_user_role: str | None = Header(default=None),
    x_client_id: str | None = Header(default=None),
) -> ClientContext:
    """Extract and validate client identity from headers.

    The production system will validate JWTs; this interim helper keeps the
    router logic focused on business rules while end-to-end auth is finalized.
    """

    if x_user_role is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Missing role header')

    normalized_role = x_user_role.lower()
    if normalized_role not in {'client', 'admin'}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Client credentials required')

    if x_client_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Missing client identifier header')

    return ClientContext(client_id=x_client_id, role=normalized_role)
