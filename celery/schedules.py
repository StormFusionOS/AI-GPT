"""Minimal Celery schedules shim for tests."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class _Crontab:
    schedule: dict[str, Any]

    def __iter__(self):  # pragma: no cover - compatibility
        yield from ()


def crontab(**kwargs: Any) -> _Crontab:
    return _Crontab(schedule=kwargs)


__all__ = ["crontab"]
