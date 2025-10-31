"""Scheduler configuration model."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class SchedulerConfig:
    """Represents a Celery beat schedule stored in the ops API."""

    task_name: str
    crontab: str
    enabled: bool = True
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None
    updated_by: str | None = None
    updated_at: datetime = field(default_factory=_utcnow)
    id: int | None = None
