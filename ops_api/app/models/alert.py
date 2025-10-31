"""Alert persistence model."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Alert:
    """Represents an operator-facing alert entry."""

    level: str
    message: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: int | None = None
