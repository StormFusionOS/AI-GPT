from typing import Generator

from fastapi import Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db


def get_db_session() -> Generator[Session, None, None]:
    yield from get_db()


async def require_admin_role(x_user_role: str | None = Header(default=None)) -> None:
    """Simple header-based guard until full authentication is wired."""

    if x_user_role is None or x_user_role.lower() != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Admin privileges required')
