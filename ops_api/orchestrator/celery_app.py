"""Celery application for orchestrated ops tasks."""
from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from typing import Any, Dict

from celery import Celery, Task
from celery.schedules import crontab
from celery.exceptions import Ignore
from celery.utils.log import get_task_logger

from app.core.config import get_settings
from app.db import session_scope
from app.models.task_runs import TaskRun
from ops_api.orchestrator.idempotency import get_idempotency_store

settings = get_settings()

celery_app = Celery(
    "ops_api",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "ops_api.orchestrator.tasks.seo",
        "ops_api.orchestrator.tasks.backup",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_default_queue="ops-default",
    task_always_eager=settings.celery_task_always_eager,
    task_eager_propagates=True,
    task_routes={
        "ops.serp_sample": {"queue": "scraper"},
        "ops.competitor_crawl": {"queue": "scraper"},
        "ops.backlink_refresh": {"queue": "scraper"},
        "ops.citation_audit": {"queue": "scraper"},
        "ops.indexnow_ping": {"queue": "ops"},
        "ops.content_generate": {"queue": "ai"},
        "ops.schema_inject": {"queue": "wp"},
        "ops.backup_nightly": {"queue": "ops"},
        "ops.backup_verify": {"queue": "ops"},
        "ops.backup_dr_test": {"queue": "ops"},
    },
    beat_schedule={
        "nightly-backup": {
            "task": "ops.backup_nightly",
            "schedule": crontab(minute=0, hour=2),
            "kwargs": {"payload": {}},
        },
        "monthly-verify": {
            "task": "ops.backup_verify",
            "schedule": crontab(minute=15, hour=3, day_of_month="1"),
            "kwargs": {"payload": {}},
        },
        "quarterly-dr-test": {
            "task": "ops.backup_dr_test",
            "schedule": crontab(minute=30, hour=4, day_of_month="1", month_of_year="1,4,7,10"),
            "kwargs": {"payload": {}},
        },
    },
)

logger = get_task_logger(__name__)


def _backoff(base_delay: int, retries: int) -> float:
    jitter = random.uniform(0, 1)
    return base_delay * (2 ** max(retries - 1, 0)) + jitter


class OrchestratorTask(Task):
    abstract = True
    max_retries = 5

    def before_start(self, task_id: str, args: tuple[Any, ...], kwargs: Dict[str, Any]) -> None:  # type: ignore[override]
        task_run_id = kwargs.get("task_run_id")
        payload = kwargs.get("payload", {})
        idempotency_key = kwargs.get("idempotency_key")
        store = get_idempotency_store()
        allowed, key = store.try_start(self.name, payload, override_key=idempotency_key)
        if not allowed:
            logger.info("Duplicate task suppressed", extra={"task": self.name, "key": key})
            if task_run_id is not None:
                with session_scope() as session:
                    run = session.get(TaskRun, task_run_id)
                    if run:
                        run.status = "skipped"
                        run.message = f"Duplicate suppressed ({key})"
                        run.finished_at = datetime.now(timezone.utc)
            raise Ignore()
        setattr(self.request, "idempotency_key", key)
        if task_run_id is None:
            return
        with session_scope() as session:
            run = session.get(TaskRun, task_run_id)
            if run:
                run.idempotency_key = key
                run.mark_running()

    def after_return(  # type: ignore[override]
        self,
        status: str,
        retval: Any,
        task_id: str,
        args: tuple[Any, ...],
        kwargs: Dict[str, Any],
        exc: BaseException | None,
    ) -> None:
        task_run_id = kwargs.get("task_run_id")
        key = getattr(self.request, "idempotency_key", kwargs.get("idempotency_key"))
        if key:
            get_idempotency_store().finish(key, outcome=status)
        if task_run_id is None:
            return
        with session_scope() as session:
            run = session.get(TaskRun, task_run_id)
            if not run:
                return
            run.retries = getattr(self.request, "retries", run.retries)
            if status == "SUCCESS":
                if retval is None:
                    message = None
                elif isinstance(retval, (str, int, float)):
                    message = str(retval)
                else:
                    message = json.dumps(retval, default=str)
                run.mark_finished("succeeded", message=message)
            elif status == "RETRY":
                run.mark_finished("retrying", message=str(exc) if exc else None)
                run.finished_at = None
            elif status == "IGNORED":
                # already marked skipped in before_start; no further action
                return
            else:
                run.mark_finished("failed", message=str(exc) if exc else None)

    def exponential_retry(self, exc: Exception, **kwargs: Any) -> None:
        retries = getattr(self.request, "retries", 0) + 1
        delay = _backoff(1, retries)
        raise self.retry(exc=exc, countdown=delay, **kwargs)


__all__ = ["celery_app", "OrchestratorTask"]

# Ensure tasks are registered when the module is imported.
from ops_api.orchestrator.tasks import backup as _backup_tasks  # noqa: F401
from ops_api.orchestrator.tasks import seo as _seo_tasks  # noqa: F401
