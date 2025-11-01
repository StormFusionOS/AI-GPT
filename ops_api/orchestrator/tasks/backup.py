"""Celery tasks for backup operations."""
from __future__ import annotations

from typing import Any, Dict

from celery.utils.log import get_task_logger

from ops_api.backup.runner import disaster_recovery_test, run_nightly_backup, verify_latest_backup
from ops_api.orchestrator.celery_app import OrchestratorTask, celery_app

logger = get_task_logger(__name__)


@celery_app.task(name="ops.backup_nightly", bind=True, base=OrchestratorTask, max_retries=3)
def nightly_backup_task(
    self: OrchestratorTask,
    *,
    task_run_id: int | None = None,
    payload: Dict[str, Any] | None = None,
    idempotency_key: str | None = None,
) -> Dict[str, Any]:
    payload = payload or {}
    try:
        result = run_nightly_backup()
    except Exception as exc:  # pragma: no cover - handled in tests through orchestrator flow
        logger.exception("Nightly backup failed")
        raise
    return {"run_id": result.id, "location": result.location, "ok": result.ok}


@celery_app.task(name="ops.backup_verify", bind=True, base=OrchestratorTask, max_retries=3)
def verify_backup_task(
    self: OrchestratorTask,
    *,
    task_run_id: int | None = None,
    payload: Dict[str, Any] | None = None,
    idempotency_key: str | None = None,
) -> Dict[str, Any]:
    payload = payload or {}
    result = verify_latest_backup()
    return {"run_id": result.id, "verify_ok": result.verify_ok, "ok": result.ok}


@celery_app.task(name="ops.backup_dr_test", bind=True, base=OrchestratorTask, max_retries=3)
def dr_test_task(
    self: OrchestratorTask,
    *,
    task_run_id: int | None = None,
    payload: Dict[str, Any] | None = None,
    idempotency_key: str | None = None,
) -> Dict[str, Any]:
    payload = payload or {}
    result = disaster_recovery_test()
    return {"run_id": result.id, "ok": result.ok}


__all__ = ["nightly_backup_task", "verify_backup_task", "dr_test_task"]
