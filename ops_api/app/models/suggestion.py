"""Suggestion persistence model."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Suggestion:
    """Represents an AI generated suggestion awaiting review."""

    type: str
    target: str
    payload_json: Dict[str, Any]
    status: str = "pending"
    created_at: datetime = field(default_factory=_utcnow)
    id: int | None = None
