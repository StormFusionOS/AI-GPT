"""Change log entry model."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ChangeLogEntry:
    """Tracks site mutations awaiting approval."""

    type: str
    target: str
    status: str = "pending"
    payload_json: Dict[str, Any] | None = None
    created_at: datetime = field(default_factory=_utcnow)
    executed_at: datetime | None = None
    executed_by: str | None = None
    decision_reason: str | None = None
    diff_snapshot: Dict[str, Any] | None = None
    anomaly_id: int | None = None
    suggestion_id: int | None = None
    id: int | None = None
