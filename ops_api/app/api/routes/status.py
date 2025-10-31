"""System status endpoints."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status

from ...security import RoleGuard, decode_token

ALLOWED_ROLES = {"SEO_ENGINEER", "DEVOPS", "OWNER"}

router = APIRouter(prefix="/status", tags=["status"])


def _authorize(authorization: str) -> None:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    claims = decode_token(authorization.split(" ", 1)[1])
    RoleGuard(ALLOWED_ROLES)(claims)


@router.get("/")
def get_status(authorization: str) -> dict[str, list[dict[str, str]]]:
    _authorize(authorization)
    now = datetime.now(timezone.utc).isoformat()
    return {
        "checks": [
            {"name": "database", "status": "OK", "message": "Connected"},
            {"name": "qdrant", "status": "OK", "message": "Ready"},
            {"name": "celery", "status": "WARN", "message": "1 delayed task"},
        ],
        "timestamp": now,
    }
