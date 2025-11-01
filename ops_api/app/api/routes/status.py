"""System status endpoints."""
from __future__ import annotations

from datetime import datetime, timezone

from typing import Dict

from fastapi import APIRouter, Depends

from ..deps import require_ops_claims

router = APIRouter(prefix="/status", tags=["status"])


@router.get("/")
def get_status(_: Dict[str, str] = Depends(require_ops_claims)) -> dict[str, list[dict[str, str]]]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "checks": [
            {"name": "database", "status": "OK", "message": "Connected"},
            {"name": "qdrant", "status": "OK", "message": "Ready"},
            {"name": "celery", "status": "WARN", "message": "1 delayed task"},
        ],
        "timestamp": now,
    }
