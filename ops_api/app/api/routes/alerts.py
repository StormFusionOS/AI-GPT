"""Alert endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from ...security import RoleGuard, decode_token

router = APIRouter(prefix="/alerts", tags=["alerts"])

_ALLOWED = {"SEO_ENGINEER", "DEVOPS", "OWNER"}


def _authorize(authorization: str) -> None:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    claims = decode_token(authorization.split(" ", 1)[1])
    RoleGuard(_ALLOWED)(claims)


@router.get("/")
def list_alerts(authorization: str) -> dict[str, list[dict[str, str]]]:
    _authorize(authorization)
    return {
        "alerts": [
            {"id": "1", "level": "CRITICAL", "message": "Backup overdue"},
            {"id": "2", "level": "WARN", "message": "New plugin vulnerability"},
        ]
    }
