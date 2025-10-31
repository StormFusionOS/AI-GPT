"""Service health snapshot model for the in-memory store."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ServiceHealth:
    """Captures the latest health probe for an infrastructure component."""

    service: str
    status: str
    latency_ms: int | None = None
    details: Dict[str, Any] | None = None
    checked_at: datetime = field(default_factory=_utcnow)
    id: int | None = None

    def update(self, *, status: str, latency_ms: int | None = None, details: Dict[str, Any] | None = None) -> None:
        self.status = status
        self.latency_ms = latency_ms
        self.details = details or {}
        self.checked_at = _utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "service": self.service,
            "status": self.status,
            "latency_ms": self.latency_ms,
            "checked_at": self.checked_at,
            "details": self.details or {},
        }
