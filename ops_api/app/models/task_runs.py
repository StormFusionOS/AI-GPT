"""Task run persistence model backed by an in-memory store."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class TaskRun:
    """Represents a single orchestrated task execution."""

    module: str
    task: str
    status: str = "queued"
    queued_at: datetime = field(default_factory=_utcnow)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    retries: int = 0
    message: str | None = None
    payload_json: Dict[str, Any] | None = None
    idempotency_key: str | None = None
    id: int | None = None

    def mark_running(self) -> None:
        self.status = "running"
        self.started_at = _utcnow()

    def mark_finished(self, status: str, message: str | None = None) -> None:
        self.status = status
        self.finished_at = _utcnow()
        if message is not None:
            self.message = message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "module": self.module,
            "task": self.task,
            "status": self.status,
            "queued_at": self.queued_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "retries": self.retries,
            "message": self.message,
        }

    def to_payload(self) -> Dict[str, Any]:
        data = dict(self.payload_json or {})
        return data
