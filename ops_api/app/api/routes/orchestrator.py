"""Orchestrator endpoints for ops console."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Mapping

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...models import ServiceHealth, TaskRun
from ...security import RoleGuard
from ..deps import get_claims, get_db
from ...schemas.orchestrator import (
    ContentGeneratePayload,
    DispatchRequest,
    DispatchResponse,
    OrchestratorHealthResponse,
    SchemaInjectPayload,
    ServiceHealthView,
    TaskRunListResponse,
    TaskRunView,
)
from ...schemas.orchestrator import (
    BacklinkRefreshPayload,
    CitationAuditPayload,
    CompetitorCrawlPayload,
    IndexNowPingPayload,
    SerpSamplePayload,
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
}

MODULE_MAP: Mapping[str, str] = {
    "serp_sample": "scraper",
    "competitor_crawl": "scraper",
    "backlink_refresh": "scraper",
    "citation_audit": "scraper",
    "indexnow_ping": "ops",
    "content_generate": "ai",
    "schema_inject": "wp",
}


def _authorise(claims: Dict[str, Any]) -> None:
    ALLOWED_ROLES(claims)


@router.get("/health", response_model=OrchestratorHealthResponse)
def get_health(
    claims: Dict[str, Any] = Depends(get_claims),
    session: Session = Depends(get_db),
) -> OrchestratorHealthResponse:
    _authorise(claims)
    stmt = select(ServiceHealth).order_by(ServiceHealth.service.asc())
    results = session.execute(stmt).scalars().all()
    services = [ServiceHealthView.from_orm(row) for row in results]
    return OrchestratorHealthResponse(services=services, generated_at=datetime.now(timezone.utc))


@router.get("/tasks", response_model=TaskRunListResponse)
def list_tasks(
    module: str | None = Query(default=None),
    status_filter: str | None = Query(alias="status", default=None),
    claims: Dict[str, Any] = Depends(get_claims),
    session: Session = Depends(get_db),
) -> TaskRunListResponse:
    _authorise(claims)
    stmt = select(TaskRun).order_by(TaskRun.queued_at.desc()).limit(200)
    if module:
        stmt = stmt.where(TaskRun.module == module)
    if status_filter:
        stmt = stmt.where(TaskRun.status == status_filter)
    runs = session.execute(stmt).scalars().all()
    return TaskRunListResponse(items=[TaskRunView.from_orm(run) for run in runs])


@router.post("/dispatch", response_model=DispatchResponse, status_code=status.HTTP_202_ACCEPTED)
def dispatch_task(
    request: DispatchRequest,
    claims: Dict[str, Any] = Depends(get_claims),
    session: Session = Depends(get_db),
) -> DispatchResponse:
    _authorise(claims)
    schema_cls = PAYLOAD_SCHEMAS.get(request.name)
    if schema_cls is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown task")
    payload_model = schema_cls(**request.payload)
    payload = payload_model.dict(exclude_none=True)
    store = get_idempotency_store()
    override_key = payload.pop("idempotency_key", None) if "idempotency_key" in payload else None
    accepted, idem_key = store.register(request.name, payload, override_key=override_key)
    module = MODULE_MAP[request.name]
    status_value = "queued" if accepted else "skipped"
    message = None if accepted else f"Duplicate request ignored ({idem_key})"
    task_run = TaskRun(module=module, task=request.name, status=status_value, payload_json=payload, message=message)
    session.add(task_run)
    session.flush()
    if not accepted:
        session.commit()
        return DispatchResponse(task_run_id=task_run.id, status="duplicate")
    celery_app.send_task(f"ops.{request.name}", kwargs={"task_run_id": task_run.id, "payload": payload})
    session.commit()
    return DispatchResponse(task_run_id=task_run.id, status="queued")
