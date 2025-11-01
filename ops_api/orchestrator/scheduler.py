"""Utilities for managing Celery beat schedules from persistence."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable

from celery import Celery
from celery.schedules import crontab

from app.db import session_scope
from app.models.scheduler import SchedulerConfig

DEFAULT_CONFIGS: Iterable[SchedulerConfig] = (
    SchedulerConfig(task_name="backup_nightly", crontab="0 2 * * *", enabled=True, updated_by="system"),
    SchedulerConfig(task_name="backup_verify", crontab="15 3 1 * *", enabled=True, updated_by="system"),
    SchedulerConfig(task_name="backup_dr_test", crontab="30 4 1 1,4,7,10 *", enabled=True, updated_by="system"),
)


def _parse_crontab(expr: str) -> crontab:
    parts = expr.split()
    if len(parts) != 5:
        raise ValueError("Cron expression must have five fields")
    minute, hour, day_of_month, month_of_year, day_of_week = parts
    return crontab(
        minute=minute,
        hour=hour,
        day_of_month=day_of_month,
        month_of_year=month_of_year,
        day_of_week=day_of_week,
        tz=timezone.utc,
    )


def compute_next_run(expr: str, *, last_run: datetime | None = None) -> datetime | None:
    try:
        schedule = _parse_crontab(expr)
    except ValueError:
        return None
    reference = last_run or datetime.now(timezone.utc)
    delta = schedule.remaining_estimate(reference)
    if delta is None:
        return None
    # Ensure the delta moves forward in time even if the scheduler is late
    if delta <= timedelta(0):
        reference = reference + timedelta(seconds=1)
        delta = schedule.remaining_estimate(reference)
        if delta is None:
            return None
    return reference + delta


def ensure_default_configs() -> None:
    with session_scope() as session:
        for template in DEFAULT_CONFIGS:
            existing = session.get_scheduler_config_by_task(template.task_name)
            if existing:
                continue
            template.next_run_at = compute_next_run(template.crontab)
            session.save_scheduler_config(template)


def refresh_beat_schedule(app: Celery) -> Dict[str, Dict[str, object]]:
    ensure_default_configs()
    schedule: Dict[str, Dict[str, object]] = {}
    with session_scope() as session:
        configs = session.list_scheduler_configs()
        for config in configs:
            if not config.enabled:
                continue
            try:
                schedule[f"dynamic-{config.task_name}"] = {
                    "task": f"ops.{config.task_name}",
                    "schedule": _parse_crontab(config.crontab),
                    "kwargs": {"payload": {}},
                }
            except ValueError:
                continue
            if config.next_run_at is None:
                config.next_run_at = compute_next_run(config.crontab, last_run=config.last_run_at)
                session.save_scheduler_config(config)
    app.conf.beat_schedule = schedule
    app.conf.last_scheduler_refresh = datetime.now(timezone.utc).isoformat()
    return schedule


def apply_schedule_update(*, task_name: str, crontab_expr: str, enabled: bool, updated_by: str | None) -> SchedulerConfig:
    next_run = compute_next_run(crontab_expr)
    with session_scope() as session:
        config = session.get_scheduler_config_by_task(task_name)
        if config is None:
            config = SchedulerConfig(
                task_name=task_name,
                crontab=crontab_expr,
                enabled=enabled,
                updated_by=updated_by,
                next_run_at=next_run,
            )
        else:
            config.crontab = crontab_expr
            config.enabled = enabled
            config.updated_by = updated_by
            config.updated_at = datetime.now(timezone.utc)
            config.next_run_at = next_run
        session.save_scheduler_config(config)
        return config


def mark_task_completion(task_name: str, finished_at: datetime | None) -> None:
    if finished_at is None:
        finished_at = datetime.now(timezone.utc)
    with session_scope() as session:
        config = session.get_scheduler_config_by_task(task_name)
        if config is None:
            return
        config.last_run_at = finished_at
        config.next_run_at = compute_next_run(config.crontab, last_run=finished_at)
        config.updated_at = datetime.now(timezone.utc)
        session.save_scheduler_config(config)
