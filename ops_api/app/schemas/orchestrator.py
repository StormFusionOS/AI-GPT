"""Pydantic models for orchestrator endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl, constr, validator

ServiceStatus = Literal["ok", "warn", "down"]


class BasePayload(BaseModel):
    idempotency_key: Optional[str] = Field(default=None, description="Override idempotency hash when provided")
    simulate: Optional[Dict[str, Any]] = Field(default=None, description="Testing hook for orchestrated tasks")


class SerpSamplePayload(BasePayload):
    keyword: constr(strip_whitespace=True, min_length=1)
    locale: constr(strip_whitespace=True, min_length=2)
    market: constr(strip_whitespace=True, min_length=2)


class CompetitorCrawlPayload(BasePayload):
    domain: HttpUrl
    depth: int = Field(ge=1, le=5)


class BacklinkRefreshPayload(BasePayload):
    domain: HttpUrl
    sample_limit: int = Field(default=100, ge=1, le=1000)


class CitationAuditPayload(BasePayload):
    business_name: constr(strip_whitespace=True, min_length=1)
    zip_code: constr(strip_whitespace=True, min_length=3)


class IndexNowPingPayload(BasePayload):
    urls: list[HttpUrl]


class ContentGeneratePayload(BasePayload):
    topic: constr(strip_whitespace=True, min_length=3)
    audience: constr(strip_whitespace=True, min_length=2)


class SchemaInjectPayload(BasePayload):
    page_url: HttpUrl
    schema_type: constr(strip_whitespace=True, min_length=3)


class BackupRunPayload(BasePayload):
    reason: constr(strip_whitespace=True, min_length=2) | None = None


class BackupVerifyPayload(BasePayload):
    pass


class BackupDrTestPayload(BasePayload):
    pass


TaskName = Literal[
    "serp_sample",
    "competitor_crawl",
    "backlink_refresh",
    "citation_audit",
    "indexnow_ping",
    "content_generate",
    "schema_inject",
    "backup_nightly",
    "backup_verify",
    "backup_dr_test",
]


class DispatchRequest(BaseModel):
    name: TaskName
    payload: Dict[str, Any]


class DispatchResponse(BaseModel):
    task_run_id: int
    status: str


class TaskRunView(BaseModel):
    id: int
    module: str
    task: str
    status: str
    queued_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    retries: int
    message: str | None

    class Config:
        orm_mode = True


class TaskRunListResponse(BaseModel):
    items: list[TaskRunView]


class ServiceHealthView(BaseModel):
    service: str
    status: ServiceStatus
    latency_ms: int | None
    checked_at: datetime
    details: Dict[str, Any] | None

    class Config:
        orm_mode = True


class OrchestratorHealthResponse(BaseModel):
    services: list[ServiceHealthView]
    generated_at: datetime


class SchedulerConfigView(BaseModel):
    id: int
    task_name: TaskName
    crontab: constr(strip_whitespace=True, min_length=5)
    enabled: bool
    last_run_at: datetime | None
    next_run_at: datetime | None
    updated_by: str | None
    updated_at: datetime


class SchedulerConfigListResponse(BaseModel):
    items: list[SchedulerConfigView]


class SchedulerConfigUpdate(BaseModel):
    task_name: TaskName
    crontab: constr(strip_whitespace=True, min_length=5)
    enabled: bool

    @validator("crontab")
    def _validate_cron(cls, value: str) -> str:
        parts = value.split()
        if len(parts) != 5:
            raise ValueError("Cron expression must contain five fields")
        return value


class SchedulerConfigUpdateRequest(BaseModel):
    configs: list[SchedulerConfigUpdate]


class SchedulerRunNowRequest(BaseModel):
    task_name: TaskName
    payload: Dict[str, Any] | None = None
