"""Celery application for orchestrated ops tasks."""
from __future__ import annotations

import random
import json
from typing import Any, Dict

from celery import Celery, Task
from celery.utils.log import get_task_logger

from app.core.config import get_settings
from app.db import session_scope
from app.models.task_runs import TaskRun

settings = get_settings()

celery_app = Celery(
    "ops_api",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "ops_api.orchestrator.tasks.seo",
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
    },
)

logger = get_task_logger(__name__)


def _backoff(base_delay: int, retries: int) -> float:
    jitter = random.uniform(0, 1)
    return base_delay * (2 ** max(retries - 1, 0)) + jitter


class OrchestratorTask(Task):
    abstract = True
    max_retries = 5

    def before_start(self, task_id: str, args: tuple[Any, ...], kwargs: Dict[str, Any]) -> None:
        task_run_id = kwargs.get("task_run_id")
        if task_run_id is None:
            return
        with session_scope() as session:
            run = session.get(TaskRun, task_run_id)
            if run:
                run.mark_running()

    def after_return(
        self,
        status: str,
        retval: Any,
        task_id: str,
        args: tuple[Any, ...],
        kwargs: Dict[str, Any],
        exc: BaseException | None,
    ) -> None:
        task_run_id = kwargs.get("task_run_id")
        if task_run_id is None:
            return
        with session_scope() as session:
            run = session.get(TaskRun, task_run_id)
            if not run:
                return
            run.retries = self.request.retries  # type: ignore[attr-defined]
            if status == "SUCCESS":
                message: str | None
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
            else:
                run.mark_finished("failed", message=str(exc) if exc else None)

    def exponential_retry(self, exc: Exception, **kwargs: Any) -> None:
        retries = self.request.retries + 1  # type: ignore[attr-defined]
        delay = _backoff(1, retries)
        raise self.retry(exc=exc, countdown=delay, **kwargs)


__all__ = ["celery_app", "OrchestratorTask"]
