"""Backup-related endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ...db import DatabaseSession
from ...schemas.backup import BackupRunListResponse, BackupRunView
from ..deps import get_db, require_ops_claims

router = APIRouter(prefix="/backups", tags=["backups"])

@router.get("/runs", response_model=BackupRunListResponse)
def list_backup_runs(
    claims = Depends(require_ops_claims),
    session: DatabaseSession = Depends(get_db),
) -> BackupRunListResponse:
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
