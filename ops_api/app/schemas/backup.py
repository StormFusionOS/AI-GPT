"""Schemas for backup run views."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class BackupRunView(BaseModel):
    id: int
    run_type: str
    location: str
    ok: bool
    verify_ok: bool | None
    bytes: int
    message: str | None
    started_at: datetime
    finished_at: datetime | None


class BackupRunListResponse(BaseModel):
    items: list[BackupRunView]
