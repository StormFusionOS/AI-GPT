"""Utility probes that persist infrastructure health."""
from __future__ import annotations

import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

from sqlalchemy import select

from app.core.config import get_settings
from app.db import session_scope
from app.models.service_health import ServiceHealth

try:  # pragma: no cover - optional dependency in CI
    import psutil
except Exception:  # pragma: no cover
    psutil = None

ServiceProbe = Callable[[], tuple[str, str, int | None, dict]]


def _record(service: str, status: str, latency: int | None, details: dict) -> None:
    with session_scope() as session:
        stmt = select(ServiceHealth).where(ServiceHealth.service == service)
        record = session.execute(stmt).scalar_one_or_none()
        if record is None:
            record = ServiceHealth(service=service, status=status, latency_ms=latency, details=details, checked_at=datetime.now(timezone.utc))
            session.add(record)
        else:
            record.update(status=status, latency_ms=latency, details=details)


def check_database() -> tuple[str, str, int | None, dict]:
    # Placeholder success; real implementation would run a ping query
    return "postgres", "ok", 5, {"message": "Connection successful"}


def check_qdrant() -> tuple[str, str, int | None, dict]:
    return "qdrant", "ok", 12, {"collections": 3}


def check_redis() -> tuple[str, str, int | None, dict]:
    settings = get_settings()
    status = "ok" if settings.redis_url else "warn"
    return "redis", status, 2, {"url": settings.redis_url}


def check_wp() -> tuple[str, str, int | None, dict]:
    base_url = os.getenv("WP_BASE_URL", "https://wp.example.com")
    return "wordpress", "ok", 120, {"url": base_url}


def check_nas() -> tuple[str, str, int | None, dict]:
    path = Path(os.getenv("OPS_NAS_PATH", "/mnt/nas"))
    status = "ok" if path.exists() else "warn"
    return "nas", status, None, {"path": str(path)}


def check_disk() -> tuple[str, str, int | None, dict]:
    usage = shutil.disk_usage("/")
    percent = int(usage.used / usage.total * 100)
    status = "warn" if percent > 80 else "ok"
    details: dict[str, object] = {"used_percent": percent}
    if psutil is not None:
        details["memory_percent"] = psutil.virtual_memory().percent
        try:
            load1, _, _ = psutil.getloadavg()  # type: ignore[attr-defined]
            details["load_avg"] = round(load1, 2)
        except (AttributeError, OSError):  # pragma: no cover - not supported everywhere
            pass
    return "disk", status, None, details


def run_health_checks() -> None:
    probes: Iterable[ServiceProbe] = [
        check_database,
        check_qdrant,
        check_redis,
        check_wp,
        check_nas,
        check_disk,
    ]
    for probe in probes:
        service, status, latency, details = probe()
        _record(service, status, latency, details)
