"""Exceptions compatible with the Celery subset used in tests."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


class Ignore(Exception):
    """Raised to signal that a task should be ignored without error."""


@dataclass
class Retry(Exception):
    exc: Exception | None
    countdown: int
    kwargs: Dict[str, Any]
