"""Alert endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ...db import DatabaseSession
from ...models import Alert
from ...schemas.alerts import AlertListResponse, AlertView
from ..deps import get_db, require_ops_claims

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("/", response_model=AlertListResponse)
def list_alerts(
    claims = Depends(require_ops_claims),
    session: DatabaseSession = Depends(get_db),
) -> AlertListResponse:
    alerts = [
        AlertView(id=alert.id or 0, level=alert.level, message=alert.message, created_at=alert.created_at)
        for alert in session.list_alerts()
    ]
    return AlertListResponse(alerts=alerts)
