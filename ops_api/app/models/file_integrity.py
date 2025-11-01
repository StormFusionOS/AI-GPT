"""File integrity tracking models for the ops data store."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class FileIntegrityRecord:
    """Baseline hash for a monitored directory or file."""

    path: str
    sha256: str
    scanned_at: datetime = field(default_factory=_utcnow)
    id: Optional[int] = None

    def touch(self) -> None:
        self.scanned_at = _utcnow()


@dataclass
class IntegrityDrift:
    """Represents a mismatch between expected and observed file hashes."""

    path: str
    expected_sha: Optional[str]
    observed_sha: Optional[str]
    reason: str


@dataclass
class IntegrityReport:
    """Summary of the most recent integrity scan."""

    generated_at: datetime
    drift: list[IntegrityDrift]
