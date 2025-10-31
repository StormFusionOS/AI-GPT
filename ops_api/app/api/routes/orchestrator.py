"""Orchestrator endpoints for ops console."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Mapping

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ...db import DatabaseSession
from ...models import TaskRun
from ...security import RoleGuard
from ..deps import get_claims, get_db
from ...schemas.orchestrator import (
    BackupDrTestPayload,
    BackupRunPayload,
    BackupVerifyPayload,
    BacklinkRefreshPayload,
    CitationAuditPayload,
    CompetitorCrawlPayload,
    ContentGeneratePayload,
    DispatchRequest,
    DispatchResponse,
    IndexNowPingPayload,
    OrchestratorHealthResponse,
    SchemaInjectPayload,
    SerpSamplePayload,
    ServiceHealthView,
    TaskRunListResponse,
    TaskRunView,
)
from ops_api.orchestrator.celery_app import celery_app
from ops_api.orchestrator.idempotency import get_idempotency_store

ALLOWED_ROLES = RoleGuard(["SEO_ENGINEER", "DEVOPS", "OWNER"])

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


PAYLOAD_SCHEMAS: Mapping[str, Any] = {
    "serp_sample": SerpSamplePayload,
    "competitor_crawl": CompetitorCrawlPayload,
    "backlink_refresh": BacklinkRefreshPayload,
    "citation_audit": CitationAuditPayload,
    "indexnow_ping": IndexNowPingPayload,
    "content_generate": ContentGeneratePayload,
    "schema_inject": SchemaInjectPayload,
    "backup_nightly": BackupRunPayload,
    "backup_verify": BackupVerifyPayload,
    "backup_dr_test": BackupDrTestPayload,
}

MODULE_MAP: Mapping[str, str] = {
    "serp_sample": "scraper",
    "competitor_crawl": "scraper",
    "backlink_refresh": "scraper",
    "citation_audit": "scraper",
    "indexnow_ping": "ops",
    "content_generate": "ai",
    "schema_inject": "wp",
    "backup_nightly": "ops",
    "backup_verify": "ops",
    "backup_dr_test": "ops",
}


def _authorise(claims: Dict[str, Any]) -> None:
    ALLOWED_ROLES(claims)


@router.get("/health", response_model=OrchestratorHealthResponse)
def get_health(
    claims: Dict[str, Any] = Depends(get_claims),
    session: DatabaseSession = Depends(get_db),
) -> OrchestratorHealthResponse:
    _authorise(claims)
    results = session.list_service_health()
    services = [
        ServiceHealthView(
            service=record.service,
            status=record.status,  # type: ignore[arg-type]
            latency_ms=record.latency_ms,
            checked_at=record.checked_at,
            details=record.details or {},
        )
        for record in results
    ]
    return OrchestratorHealthResponse(services=services, generated_at=datetime.now(timezone.utc))


@router.get("/tasks", response_model=TaskRunListResponse)
def list_tasks(
    module: str | None = Query(default=None),
    status_filter: str | None = Query(alias="status", default=None),
    claims: Dict[str, Any] = Depends(get_claims),
    session: DatabaseSession = Depends(get_db),
) -> TaskRunListResponse:
    _authorise(claims)
    runs = session.list_task_runs(module=module, status=status_filter, limit=200)
    return TaskRunListResponse(
        items=[
            TaskRunView(
                id=run.id or 0,
                module=run.module,
                task=run.task,
                status=run.status,
                queued_at=run.queued_at,
                started_at=run.started_at,
                finished_at=run.finished_at,
                retries=run.retries,
                message=run.message,
            )
            for run in runs
        ]
    )


@router.post("/dispatch", response_model=DispatchResponse, status_code=status.HTTP_202_ACCEPTED)
def dispatch_task(
    request: DispatchRequest,
    claims: Dict[str, Any] = Depends(get_claims),
    session: DatabaseSession = Depends(get_db),
) -> DispatchResponse:
    _authorise(claims)
    schema_cls = PAYLOAD_SCHEMAS.get(request.name)
    if schema_cls is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown task")
    payload_model = schema_cls(**request.payload)
    payload = payload_model.dict(exclude_none=True)
    override_key = payload.pop("idempotency_key", None) if "idempotency_key" in payload else None
    store = get_idempotency_store()
    accepted, idem_key = store.reserve(request.name, payload, override_key=override_key)
    module = MODULE_MAP[request.name]
    status_value = "queued" if accepted else "skipped"
    message = None if accepted else f"Duplicate request ignored ({idem_key})"
    task_run = TaskRun(
        module=module,
        task=request.name,
        status=status_value,
        payload_json=payload,
        message=message,
        idempotency_key=idem_key,
    )
    session.add(task_run)
    if not accepted:
        return DispatchResponse(task_run_id=task_run.id or 0, status="duplicate")
    celery_app.send_task(
        f"ops.{request.name}",
        kwargs={"task_run_id": task_run.id, "payload": payload, "idempotency_key": idem_key},
    )
    return DispatchResponse(task_run_id=task_run.id or 0, status="queued")
