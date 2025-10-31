"""Minimal Celery schedules shim for tests."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any


@dataclass
class _Crontab:
    minute: str = "*"
    hour: str = "*"
    day_of_month: str = "*"
    month_of_year: str = "*"
    day_of_week: str = "*"
    tz: Any | None = None

    def __post_init__(self) -> None:
        self._orig_minute = self.minute
        self._orig_hour = self.hour

    def remaining_estimate(self, last_run_at: datetime | None) -> timedelta:
        # The real Celery implementation calculates the precise delta; here we
        # return a small positive interval so callers can schedule follow-up work.
        return timedelta(minutes=1)

    def __iter__(self):  # pragma: no cover - compatibility shim
        yield from ()


def crontab(
    *,
    minute: str = "*",
    hour: str = "*",
    day_of_month: str = "*",
    month_of_year: str = "*",
    day_of_week: str = "*",
    tz: Any | None = None,
    **_: Any,
) -> _Crontab:
    return _Crontab(
        minute=minute,
        hour=hour,
        day_of_month=day_of_month,
        month_of_year=month_of_year,
        day_of_week=day_of_week,
        tz=tz,
    )


__all__ = ["crontab"]
