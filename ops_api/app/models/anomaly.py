"""Anomaly persistence model."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Anomaly:
    """Represents a detected SEO anomaly awaiting remediation."""

    page_id: str
    type: str
    summary: str
    proposed_actions: List[str]
    created_at: datetime = field(default_factory=_utcnow)
    id: int | None = None


__all__ = ["Anomaly"]
