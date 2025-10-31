"""Celery task implementations for SEO and ops jobs."""
from __future__ import annotations

from typing import Any, Dict

from celery.utils.log import get_task_logger

from ops_api.orchestrator.celery_app import OrchestratorTask, celery_app

logger = get_task_logger(__name__)


class TransientTaskError(Exception):
    """Raised when a retryable error occurs."""


class FatalTaskError(Exception):
    """Raised when work should not be retried."""


def _simulate(payload: Dict[str, Any]) -> None:
    simulation = payload.get("simulate", {})
    if not simulation:
        return
    if simulation.get("fatal_error"):
        raise FatalTaskError("Fatal error requested")
    failures = simulation.get("transient_failures", 0)
    if failures > 0:
        simulation["transient_failures"] = failures - 1
        raise TransientTaskError("Transient failure requested")


@celery_app.task(name="ops.serp_sample", bind=True, base=OrchestratorTask, max_retries=5)
def serp_sample(self: OrchestratorTask, *, task_run_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        _simulate(payload)
    except TransientTaskError as exc:
        self.exponential_retry(exc, kwargs={"task_run_id": task_run_id, "payload": payload})
    except FatalTaskError as exc:
        raise exc
    result = {"status": "ok", "keywords_processed": [payload.get("keyword", "")]}
    logger.info("SERP sample complete", extra=result)
    return result


@celery_app.task(name="ops.competitor_crawl", bind=True, base=OrchestratorTask, max_retries=5)
def competitor_crawl(self: OrchestratorTask, *, task_run_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        _simulate(payload)
    except TransientTaskError as exc:
        self.exponential_retry(exc, kwargs={"task_run_id": task_run_id, "payload": payload})
    except FatalTaskError as exc:
        raise exc
    logger.info("Competitor crawl complete", extra={"domain": payload.get("domain")})
    return {"status": "ok"}


@celery_app.task(name="ops.backlink_refresh", bind=True, base=OrchestratorTask, max_retries=5)
def backlink_refresh(self: OrchestratorTask, *, task_run_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        _simulate(payload)
    except TransientTaskError as exc:
        self.exponential_retry(exc, kwargs={"task_run_id": task_run_id, "payload": payload})
    except FatalTaskError as exc:
        raise exc
    logger.info("Backlink refresh finished", extra={"domain": payload.get("domain")})
    return {"status": "ok"}


@celery_app.task(name="ops.citation_audit", bind=True, base=OrchestratorTask, max_retries=5)
def citation_audit(self: OrchestratorTask, *, task_run_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        _simulate(payload)
    except TransientTaskError as exc:
        self.exponential_retry(exc, kwargs={"task_run_id": task_run_id, "payload": payload})
    except FatalTaskError as exc:
        raise exc
    logger.info("Citation audit complete", extra={"business": payload.get("business_name")})
    return {"status": "ok"}


@celery_app.task(name="ops.indexnow_ping", bind=True, base=OrchestratorTask, max_retries=5)
def indexnow_ping(self: OrchestratorTask, *, task_run_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        _simulate(payload)
    except TransientTaskError as exc:
        self.exponential_retry(exc, kwargs={"task_run_id": task_run_id, "payload": payload})
    except FatalTaskError as exc:
        raise exc
    logger.info("IndexNow ping complete", extra={"urls": payload.get("urls")})
    return {"status": "ok"}


@celery_app.task(name="ops.content_generate", bind=True, base=OrchestratorTask, max_retries=5)
def content_generate(self: OrchestratorTask, *, task_run_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        _simulate(payload)
    except TransientTaskError as exc:
        self.exponential_retry(exc, kwargs={"task_run_id": task_run_id, "payload": payload})
    except FatalTaskError as exc:
        raise exc
    logger.info("Content generated", extra={"topic": payload.get("topic")})
    return {"status": "ok"}


@celery_app.task(name="ops.schema_inject", bind=True, base=OrchestratorTask, max_retries=5)
def schema_inject(self: OrchestratorTask, *, task_run_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        _simulate(payload)
    except TransientTaskError as exc:
        self.exponential_retry(exc, kwargs={"task_run_id": task_run_id, "payload": payload})
    except FatalTaskError as exc:
        raise exc
    logger.info("Schema injected", extra={"page": payload.get("page_url")})
    return {"status": "ok"}


__all__ = [
    "serp_sample",
    "competitor_crawl",
    "backlink_refresh",
    "citation_audit",
    "indexnow_ping",
    "content_generate",
    "schema_inject",
    "TransientTaskError",
    "FatalTaskError",
]
