"""Scheduler endpoints for managing Celery beat dynamically."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from ...db import DatabaseSession
from ...models import SchedulerConfig, TaskRun
from ...schemas.orchestrator import (
    DispatchResponse,
    SchedulerConfigListResponse,
    SchedulerConfigUpdateRequest,
    SchedulerConfigView,
    SchedulerRunNowRequest,
    TaskName,
)
from ..deps import get_db, require_ops_claims
from ops_api.orchestrator.celery_app import celery_app
from ops_api.orchestrator.idempotency import get_idempotency_store
from ops_api.orchestrator.scheduler import apply_schedule_update, refresh_beat_schedule
from .orchestrator import MODULE_MAP, PAYLOAD_SCHEMAS

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


def _to_view(config: SchedulerConfig) -> SchedulerConfigView:
    return SchedulerConfigView(
        id=config.id or 0,
        task_name=config.task_name,  # type: ignore[arg-type]
        crontab=config.crontab,
        enabled=config.enabled,
        last_run_at=config.last_run_at,
        next_run_at=config.next_run_at,
        updated_by=config.updated_by,
        updated_at=config.updated_at,
    )


@router.get("/configs", response_model=SchedulerConfigListResponse)
def list_configs(
    claims: Dict[str, Any] = Depends(require_ops_claims),
    session: DatabaseSession = Depends(get_db),
) -> SchedulerConfigListResponse:
    configs = session.list_scheduler_configs()
    return SchedulerConfigListResponse(items=[_to_view(config) for config in configs])


@router.put("/configs", response_model=SchedulerConfigListResponse)
def update_configs(
    request: SchedulerConfigUpdateRequest,
    claims: Dict[str, Any] = Depends(require_ops_claims),
    session: DatabaseSession = Depends(get_db),
) -> SchedulerConfigListResponse:
    updated_by = claims.get("sub") or claims.get("email") or "ops"
    for config in request.configs:
        if config.task_name not in PAYLOAD_SCHEMAS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown task")
        apply_schedule_update(
            task_name=config.task_name,
            crontab_expr=config.crontab,
            enabled=config.enabled,
            updated_by=updated_by,
        )
    refresh_beat_schedule(celery_app)
    configs = session.list_scheduler_configs()
    return SchedulerConfigListResponse(items=[_to_view(config) for config in configs])


@router.post("/run-now", response_model=DispatchResponse, status_code=status.HTTP_202_ACCEPTED)
def run_now(
    request: SchedulerRunNowRequest,
    claims: Dict[str, Any] = Depends(require_ops_claims),
    session: DatabaseSession = Depends(get_db),
) -> DispatchResponse:
    schema_cls = PAYLOAD_SCHEMAS.get(request.task_name)
    if schema_cls is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown task")
    payload_model = schema_cls(**(request.payload or {}))
    payload = payload_model.dict(exclude_none=True)
    override_key = payload.pop("idempotency_key", None) if "idempotency_key" in payload else None
    store = get_idempotency_store()
    accepted, idem_key = store.reserve(request.task_name, payload, override_key=override_key)
    module = MODULE_MAP[request.task_name]
    status_value = "queued" if accepted else "skipped"
    message = None if accepted else f"Duplicate request ignored ({idem_key})"
    task_run = TaskRun(
        module=module,
        task=request.task_name,
        status=status_value,
        payload_json=payload,
        message=message,
        idempotency_key=idem_key,
    )
    session.add(task_run)
    if not accepted:
        return DispatchResponse(task_run_id=task_run.id or 0, status="duplicate")
    celery_app.send_task(
        f"ops.{request.task_name}",
        kwargs={"task_run_id": task_run.id, "payload": payload, "idempotency_key": idem_key},
    )
    return DispatchResponse(task_run_id=task_run.id or 0, status="queued")
