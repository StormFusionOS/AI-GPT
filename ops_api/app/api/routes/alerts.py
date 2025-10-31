"""Alert endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ...db import DatabaseSession
from ...models import Alert
from ...schemas.alerts import AlertListResponse, AlertView
from ...security import RoleGuard
from ..deps import get_claims, get_db

router = APIRouter(prefix="/alerts", tags=["alerts"])

_ALLOWED = RoleGuard(["SEO_ENGINEER", "DEVOPS", "OWNER"])


@router.get("/", response_model=AlertListResponse)
def list_alerts(
    claims = Depends(get_claims),  # type: ignore[assignment]
    session: DatabaseSession = Depends(get_db),
) -> AlertListResponse:
    _ALLOWED(claims)
    alerts = [
        AlertView(id=alert.id or 0, level=alert.level, message=alert.message, created_at=alert.created_at)
        for alert in session.list_alerts()
    ]
    return AlertListResponse(alerts=alerts)
