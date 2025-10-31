"""Backup-related endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ...db import DatabaseSession
from ...schemas.backup import BackupRunListResponse, BackupRunView
from ...security import RoleGuard
from ..deps import get_claims, get_db

router = APIRouter(prefix="/backups", tags=["backups"])

_ALLOWED = RoleGuard(["SEO_ENGINEER", "DEVOPS", "OWNER"])


@router.get("/runs", response_model=BackupRunListResponse)
def list_backup_runs(
    claims = Depends(get_claims),  # type: ignore[assignment]
    session: DatabaseSession = Depends(get_db),
) -> BackupRunListResponse:
    _ALLOWED(claims)
    runs = [
        BackupRunView(
            id=run.id or 0,
            run_type=run.run_type,
            location=run.location,
            ok=run.ok,
            verify_ok=run.verify_ok,
            bytes=run.bytes,
            message=run.message,
            started_at=run.started_at,
            finished_at=run.finished_at,
        )
        for run in session.list_backup_runs()
    ]
    return BackupRunListResponse(items=runs)
