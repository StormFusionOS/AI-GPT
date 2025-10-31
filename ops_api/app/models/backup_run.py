"""Backup run persistence model."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class BackupRun:
    """Represents the result of a backup, verify, or DR task."""

    run_type: str
    location: str
    ok: bool = True
    verify_ok: bool | None = None
    bytes: int = 0
    message: Optional[str] = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None
    id: int | None = None

    def mark_finished(self, *, ok: bool | None = None, verify_ok: bool | None = None, message: str | None = None) -> None:
        if ok is not None:
            self.ok = ok
        if verify_ok is not None:
            self.verify_ok = verify_ok
        if message is not None:
            self.message = message
        self.finished_at = datetime.now(timezone.utc)
