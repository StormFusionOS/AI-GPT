"""Tests for scheduler configuration endpoints."""
from __future__ import annotations

from datetime import datetime, timezone

from app.api.routes.scheduler import list_configs, run_now, update_configs
from app.db import DatabaseSession
from app.models.task_runs import TaskRun
from app.schemas.orchestrator import (
    SchedulerConfigUpdate,
    SchedulerConfigUpdateRequest,
    SchedulerRunNowRequest,
)
from ops_api.orchestrator.celery_app import celery_app


def _auth() -> dict[str, str]:
    return {"sub": "ops@example.com", "role": "SEO_ENGINEER"}


def test_list_configs_returns_defaults(db_session: DatabaseSession) -> None:
    response = list_configs(claims=_auth(), session=db_session)
    assert response.items
    tasks = {item.task_name for item in response.items}
    assert {"backup_nightly", "backup_verify", "backup_dr_test"}.issubset(tasks)


def test_update_config_refreshes_schedule(db_session: DatabaseSession) -> None:
    request = SchedulerConfigUpdateRequest(
        configs=[SchedulerConfigUpdate(task_name="backup_nightly", crontab="5 1 * * *", enabled=True)]
    )
    response = update_configs(request=request, claims=_auth(), session=db_session)
    config = next(item for item in response.items if item.task_name == "backup_nightly")
    assert config.crontab == "5 1 * * *"
    entry = celery_app.conf.beat_schedule.get("dynamic-backup_nightly")
    assert entry is not None
    schedule = entry["schedule"]
    assert getattr(schedule, "_orig_minute", None) == "5"
    refreshed = celery_app.conf.last_scheduler_refresh
    assert refreshed is not None
    refreshed_dt = datetime.fromisoformat(refreshed)
    assert (datetime.now(timezone.utc) - refreshed_dt).total_seconds() < 60


def test_run_now_enqueues_task(db_session: DatabaseSession) -> None:
    request = SchedulerRunNowRequest(task_name="backup_verify", payload={})
    response = run_now(request=request, claims=_auth(), session=db_session)
    assert response.status in {"queued", "duplicate"}
    run = db_session.get(TaskRun, response.task_run_id)
    if run is None:
        run = next((item for item in db_session.list_task_runs() if item.id == response.task_run_id), None)
    assert run is not None
    assert run.task == "backup_verify"
