"""System monitoring, scheduling, and security endpoints."""

from __future__ import annotations

import json
import re
import shutil
from collections import deque
from datetime import UTC, datetime, timedelta
from hashlib import sha1
from pathlib import Path
from typing import Any, Iterable, Literal

import psutil
import redis
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, require_admin_role
from app.core.config import settings
from app.core.scheduler import ScheduledJob, list_jobs, set_job_enabled, trigger_job
from app.security.integrity import IntegrityIssue, IntegrityMonitor
from app.security.wp_scanner import SiteSecurityReport, scan_wordpress_plugins


router = APIRouter(tags=['system'])


class ResourceUsage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    cpu_percent: float = Field(alias='cpuPercent')
    memory_percent: float = Field(alias='memoryPercent')
    disk_percent: float = Field(alias='diskPercent')
    disk_free_bytes: int = Field(alias='diskFreeBytes')


class StatusItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    status: Literal['ok', 'warn', 'error']
    message: str
    value: str | None = None
    checked_at: datetime = Field(alias='checkedAt')


class IntegrityFindingModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    path: str
    status: str
    message: str
    observed_at: datetime = Field(alias='observedAt')


class WordPressPluginModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    slug: str
    name: str
    installed_version: str = Field(alias='installedVersion')
    latest_version: str | None = Field(default=None, alias='latestVersion')
    status: str
    severity: str
    notes: str | None = Field(default=None)


class WordPressReportModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    site: str
    base_url: str = Field(alias='baseUrl')
    checked_at: datetime = Field(alias='checkedAt')
    plugins: list[WordPressPluginModel]
    errors: list[str]


class LogSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    app_errors: int = Field(alias='appErrors')
    task_errors: int = Field(alias='taskErrors')


class SystemStatusResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    generated_at: datetime = Field(alias='generatedAt')
    checks: list[StatusItem]
    resource_usage: ResourceUsage
    last_backup_at: datetime | None = Field(default=None, alias='lastBackupAt')
    last_scraper_run_at: datetime | None = Field(default=None, alias='lastScraperRunAt')
    integrity_findings: list[IntegrityFindingModel] = Field(alias='integrityFindings')
    wordpress: list[WordPressReportModel]
    log_summary: LogSummary = Field(alias='logSummary')


class AlertModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    message: str
    severity: Literal['info', 'warning', 'critical']
    source: str
    created_at: datetime = Field(alias='createdAt')


class ScheduleModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    cron: str
    enabled: bool
    description: str | None = None
    last_run: datetime | None = Field(default=None, alias='lastRun')
    next_run: datetime | None = Field(default=None, alias='nextRun')
    last_status: str | None = Field(default=None, alias='lastStatus')


class LogTailResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    path: str
    lines: list[str]
    generated_at: datetime = Field(alias='generatedAt')


class StructuredLogLine(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    level: Literal['INFO', 'WARN', 'ERROR']
    timestamp: datetime
    message: str
    domain: str | None = None
    job_id: str | None = Field(default=None, alias='jobId')
    reason_code: str | None = Field(default=None, alias='reasonCode')


class LogsResponseModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[StructuredLogLine]
    next_cursor: str | None = Field(default=None, alias='nextCursor')


def _tail_file(path: Path, lines: int) -> list[str]:
    if not path.exists():
        return []
    deque_buffer: deque[str] = deque(maxlen=lines)
    with path.open('r', encoding='utf-8', errors='ignore') as handle:
        for line in handle:
            deque_buffer.append(line.rstrip('\n'))
    return list(deque_buffer)


def _parse_structured_logs(lines: Iterable[str]) -> list[StructuredLogLine]:
    parsed: list[StructuredLogLine] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        payload: dict[str, Any] | None = None
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            payload = None

        if isinstance(payload, dict):
            timestamp = payload.get('timestamp') or payload.get('time') or datetime.now(tz=UTC).isoformat()
            level = str(payload.get('level', 'INFO')).upper()
            message = str(payload.get('event') or payload.get('message') or line)
            parsed.append(
                StructuredLogLine(
                    id=sha1(line.encode('utf-8')).hexdigest(),
                    level='ERROR' if 'ERR' in level else ('WARN' if 'WARN' in level else 'INFO'),
                    timestamp=datetime.fromisoformat(timestamp) if isinstance(timestamp, str) else datetime.now(tz=UTC),
                    message=message,
                    domain=payload.get('domain'),
                    jobId=payload.get('job_id') or payload.get('jobId'),
                    reasonCode=payload.get('reason_code') or payload.get('reasonCode'),
                )
            )
            continue

        # Fallback plain-text parsing
        match = re.match(r'^(?P<ts>\S+)\s+\[(?P<level>\w+)\]\s+(?P<message>.*)$', line)
        if match:
            ts = match.group('ts')
            level = match.group('level').upper()
            message = match.group('message')
            timestamp = datetime.fromisoformat(ts) if _looks_like_iso(ts) else datetime.now(tz=UTC)
            parsed.append(
                StructuredLogLine(
                    id=sha1(line.encode('utf-8')).hexdigest(),
                    level='ERROR' if level == 'ERROR' else ('WARN' if level == 'WARN' else 'INFO'),
                    timestamp=timestamp,
                    message=message,
                )
            )
        else:
            parsed.append(
                StructuredLogLine(
                    id=sha1(line.encode('utf-8')).hexdigest(),
                    level='INFO',
                    timestamp=datetime.now(tz=UTC),
                    message=line,
                )
            )
    return parsed


def _looks_like_iso(value: str) -> bool:
    try:
        datetime.fromisoformat(value)
        return True
    except ValueError:
        return False


def _count_keyword_hits(lines: Iterable[str]) -> int:
    keywords = tuple(settings.log_alert_keywords)
    total = 0
    for line in lines:
        if any(keyword in line for keyword in keywords):
            total += 1
    return total


def _find_last_backup() -> datetime | None:
    backup_root = Path(settings.backup_root).expanduser()
    if not backup_root.exists():
        return None
    archives = sorted(backup_root.glob('backup_*.tar.gz'), key=lambda path: path.stat().st_mtime, reverse=True)
    if not archives:
        return None
    return datetime.fromtimestamp(archives[0].stat().st_mtime, tz=UTC)


def _find_last_scraper_run(session: Session) -> datetime | None:
    try:
        result = session.execute(
            text("""
                SELECT started_at
                FROM task_logs
                WHERE task_name LIKE 'scraper%'
                ORDER BY started_at DESC
                LIMIT 1
            """),
        )
    except SQLAlchemyError:
        return None
    row = result.first()
    if row and row[0]:
        started_at = row[0]
        if isinstance(started_at, datetime):
            return started_at if started_at.tzinfo else started_at.replace(tzinfo=UTC)
    return None


def _build_status_checks(session: Session) -> list[StatusItem]:
    checks: list[StatusItem] = []
    now = datetime.now(tz=UTC)

    # Database
    try:
        start = datetime.now(tz=UTC)
        session.execute(text('SELECT 1'))
        duration_ms = (datetime.now(tz=UTC) - start).total_seconds() * 1000
        checks.append(
            StatusItem(
                id='database',
                name='PostgreSQL',
                status='ok',
                message=f'Responded in {duration_ms:.1f} ms',
                value=f'{duration_ms:.1f} ms',
                checked_at=now,
            )
        )
    except SQLAlchemyError as exc:
        checks.append(
            StatusItem(
                id='database',
                name='PostgreSQL',
                status='error',
                message=f'Database connectivity failed: {exc}',
                checked_at=now,
            )
        )

    # Qdrant
    try:
        client = QdrantClient(url=str(settings.qdrant_url), api_key=settings.qdrant_api_key)
        collections = client.get_collections()
        checks.append(
            StatusItem(
                id='qdrant',
                name='Qdrant',
                status='ok',
                message=f"{len(collections.collections)} collections available",
                value=str(len(collections.collections)),
                checked_at=now,
            )
        )
    except UnexpectedResponse as exc:
        checks.append(
            StatusItem(
                id='qdrant',
                name='Qdrant',
                status='error',
                message=f'Qdrant API error: {exc}',
                checked_at=now,
            )
        )
    except Exception as exc:  # pragma: no cover - network failure path
        checks.append(
            StatusItem(
                id='qdrant',
                name='Qdrant',
                status='error',
                message=f'Qdrant unreachable: {exc}',
                checked_at=now,
            )
        )

    # Redis / Celery broker
    try:
        redis_client = redis.Redis.from_url(str(settings.redis_url), socket_connect_timeout=2, socket_timeout=2)
        pong = redis_client.ping()
        checks.append(
            StatusItem(
                id='redis',
                name='Redis Broker',
                status='ok' if pong else 'warn',
                message='Broker reachable' if pong else 'Broker ping returned no response',
                checked_at=now,
            )
        )
    except redis.RedisError as exc:  # pragma: no cover - network failure path
        checks.append(
            StatusItem(
                id='redis',
                name='Redis Broker',
                status='error',
                message=f'Redis ping failed: {exc}',
                checked_at=now,
            )
        )

    # Disk usage
    media_path = Path(settings.media_root).expanduser()
    media_path.mkdir(parents=True, exist_ok=True)
    usage = shutil.disk_usage(media_path)
    percent = usage.used / usage.total if usage.total else 0
    status: Literal['ok', 'warn', 'error']
    if percent >= 0.9:
        status = 'error'
    elif percent >= 0.75:
        status = 'warn'
    else:
        status = 'ok'
    checks.append(
        StatusItem(
            id='disk',
            name='Disk Usage',
            status=status,
            message=f"{percent * 100:.1f}% used", 
            value=f"{percent * 100:.1f}%",
            checked_at=now,
        )
    )

    return checks


def _resource_usage() -> ResourceUsage:
    cpu_percent = psutil.cpu_percent(interval=None)
    memory_percent = psutil.virtual_memory().percent
    media_path = Path(settings.media_root).expanduser()
    media_path.mkdir(parents=True, exist_ok=True)
    usage = shutil.disk_usage(media_path)
    disk_percent = (usage.used / usage.total) * 100 if usage.total else 0.0
    return ResourceUsage(
        cpu_percent=cpu_percent,
        memory_percent=memory_percent,
        disk_percent=disk_percent,
        disk_free_bytes=usage.free,
    )


def _convert_integrity_findings(findings: list[IntegrityIssue]) -> list[IntegrityFindingModel]:
    return [
        IntegrityFindingModel(
            path=item.path,
            status=item.status,
            message=item.message,
            observed_at=item.observed_at,
        )
        for item in findings
    ]


def _convert_wp_reports(reports: list[SiteSecurityReport]) -> list[WordPressReportModel]:
    converted: list[WordPressReportModel] = []
    for report in reports:
        plugins = [
            WordPressPluginModel(
                slug=plugin.slug,
                name=plugin.name,
                installed_version=plugin.installed_version,
                latest_version=plugin.latest_version,
                status=plugin.status,
                severity=plugin.severity,
                notes=plugin.notes,
            )
            for plugin in report.plugins
        ]
        converted.append(
            WordPressReportModel(
                site=report.site,
                base_url=report.base_url,
                checked_at=report.checked_at,
                plugins=plugins,
                errors=report.errors,
            )
        )
    return converted


def _collect_alerts(
    status: SystemStatusResponse,
    integrity_findings: list[IntegrityIssue],
    wp_reports: list[SiteSecurityReport],
    log_tail_app: list[str],
    log_tail_tasks: list[str],
) -> list[AlertModel]:
    alerts: list[AlertModel] = []
    now = status.generated_at

    for check in status.checks:
        if check.status == 'error':
            alerts.append(
                AlertModel(
                    id=_alert_id('status', check.id),
                    message=f"{check.name}: {check.message}",
                    severity='critical',
                    source=f'status:{check.id}',
                    created_at=now,
                )
            )
        elif check.status == 'warn':
            alerts.append(
                AlertModel(
                    id=_alert_id('status', check.id),
                    message=f"{check.name}: {check.message}",
                    severity='warning',
                    source=f'status:{check.id}',
                    created_at=now,
                )
            )

    if status.last_backup_at is None or now - status.last_backup_at > timedelta(hours=36):
        alerts.append(
            AlertModel(
                id=_alert_id('backup', 'stale'),
                message='No recent backup detected in the last 36 hours',
                severity='critical',
                source='backup',
                created_at=now,
            )
        )

    if status.last_scraper_run_at is None or now - status.last_scraper_run_at > timedelta(hours=6):
        alerts.append(
            AlertModel(
                id=_alert_id('scraper', 'inactive'),
                message='Scraper tasks have not completed within the last 6 hours',
                severity='warning',
                source='scraper',
                created_at=now,
            )
        )

    for finding in integrity_findings:
        if finding.status in {'changed', 'missing', 'removed'}:
            alerts.append(
                AlertModel(
                    id=_alert_id('integrity', finding.path),
                    message=f'Integrity change detected for {finding.path}: {finding.message}',
                    severity='critical',
                    source='integrity',
                    created_at=now,
                )
            )

    for report in wp_reports:
        for plugin in report.plugins:
            if plugin.status in {'outdated', 'missing'}:
                severity = 'critical' if plugin.status == 'missing' else 'warning'
                alerts.append(
                    AlertModel(
                        id=_alert_id('wordpress', f'{report.site}:{plugin.slug}'),
                        message=f"{report.site}: {plugin.name} is {plugin.status} (installed {plugin.installed_version}, latest {plugin.latest_version or 'unknown'})",
                        severity='critical' if plugin.severity == 'critical' else severity,
                        source='wordpress',
                        created_at=now,
                    )
                )

        for error in report.errors:
            alerts.append(
                AlertModel(
                    id=_alert_id('wordpress', f'{report.site}:error:{error}'),
                    message=f'{report.site}: {error}',
                    severity='warning',
                    source='wordpress',
                    created_at=now,
                )
            )

    app_hits = _count_keyword_hits(log_tail_app)
    task_hits = _count_keyword_hits(log_tail_tasks)
    if app_hits:
        alerts.append(
            AlertModel(
                id=_alert_id('logs', 'app'),
                message=f'{app_hits} error lines detected in application logs',
                severity='warning',
                source='logs:app',
                created_at=now,
            )
        )
    if task_hits:
        alerts.append(
            AlertModel(
                id=_alert_id('logs', 'tasks'),
                message=f'{task_hits} error lines detected in task logs',
                severity='warning',
                source='logs:tasks',
                created_at=now,
            )
        )

    return alerts


def _alert_id(*components: str) -> str:
    digest = sha1(':'.join(components).encode('utf-8')).hexdigest()
    return digest


def _load_acknowledged_alerts() -> set[str]:
    path = Path(settings.alerts_state_path).expanduser()
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError:
        return set()
    return set(data)


def _store_acknowledged_alerts(alert_ids: set[str]) -> None:
    path = Path(settings.alerts_state_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sorted(alert_ids)), encoding='utf-8')


async def _build_status_payload(session: Session) -> tuple[SystemStatusResponse, list[IntegrityIssue], list[SiteSecurityReport], list[str], list[str]]:
    checks = _build_status_checks(session)
    resource_usage = _resource_usage()
    monitor = IntegrityMonitor(watch_paths=settings.integrity_watch_paths, state_file=settings.integrity_state_path)
    integrity_findings, _ = monitor.scan(update_baseline=False)
    wp_reports = await scan_wordpress_plugins()
    app_log_lines = _tail_file(Path(settings.app_log_path).expanduser(), 200)
    task_log_lines = _tail_file(Path(settings.task_log_path).expanduser(), 200)
    log_summary = LogSummary(
        app_errors=_count_keyword_hits(app_log_lines),
        task_errors=_count_keyword_hits(task_log_lines),
    )
    status_response = SystemStatusResponse(
        generated_at=datetime.now(tz=UTC),
        checks=checks,
        resource_usage=resource_usage,
        last_backup_at=_find_last_backup(),
        last_scraper_run_at=_find_last_scraper_run(session),
        integrity_findings=_convert_integrity_findings(integrity_findings),
        wordpress=_convert_wp_reports(wp_reports),
        log_summary=log_summary,
    )
    return status_response, integrity_findings, wp_reports, app_log_lines, task_log_lines


@router.get('/status', response_model=SystemStatusResponse, dependencies=[Depends(require_admin_role)])
async def get_system_status(session: Session = Depends(get_db_session)) -> SystemStatusResponse:
    status_response, _, _, _, _ = await _build_status_payload(session)
    return status_response


@router.get('/logs/app', response_model=LogTailResponse, dependencies=[Depends(require_admin_role)])
async def get_application_logs(lines: int = Query(default=200, ge=1, le=2000)) -> LogTailResponse:
    path = Path(settings.app_log_path).expanduser()
    return LogTailResponse(path=str(path), lines=_tail_file(path, lines), generated_at=datetime.now(tz=UTC))


@router.get('/logs/tasks', response_model=LogTailResponse, dependencies=[Depends(require_admin_role)])
async def get_task_logs(lines: int = Query(default=200, ge=1, le=2000)) -> LogTailResponse:
    path = Path(settings.task_log_path).expanduser()
    return LogTailResponse(path=str(path), lines=_tail_file(path, lines), generated_at=datetime.now(tz=UTC))


@router.get('/logs', response_model=LogsResponseModel, dependencies=[Depends(require_admin_role)])
async def get_structured_logs(lines: int = Query(default=200, ge=1, le=2000)) -> LogsResponseModel:
    path = Path(settings.app_log_path).expanduser()
    parsed = _parse_structured_logs(_tail_file(path, lines))
    return LogsResponseModel(items=parsed, next_cursor=None)


@router.get('/alerts', response_model=list[AlertModel], dependencies=[Depends(require_admin_role)])
async def get_alerts(session: Session = Depends(get_db_session)) -> list[AlertModel]:
    status_response, integrity_findings, wp_reports, app_log_lines, task_log_lines = await _build_status_payload(session)
    alerts = _collect_alerts(status_response, integrity_findings, wp_reports, app_log_lines, task_log_lines)
    acknowledged = _load_acknowledged_alerts()
    return [alert for alert in alerts if alert.id not in acknowledged]


@router.post('/alerts/{alert_id}/acknowledge', status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin_role)])
async def acknowledge_alert(alert_id: str) -> None:
    acknowledged = _load_acknowledged_alerts()
    acknowledged.add(alert_id)
    _store_acknowledged_alerts(acknowledged)


def _to_schedule_model(job: ScheduledJob) -> ScheduleModel:
    return ScheduleModel(
        id=job.id,
        name=job.name,
        cron=job.cron,
        enabled=job.enabled,
        description=job.description,
        last_run=job.last_run,
        next_run=job.next_run,
        last_status=job.last_status,
    )


@router.get('/schedules', response_model=list[ScheduleModel], dependencies=[Depends(require_admin_role)])
async def list_schedules() -> list[ScheduleModel]:
    jobs = list_jobs(refresh_next_run=True)
    return [_to_schedule_model(job) for job in jobs]


@router.post('/schedules/{job_id}/toggle', response_model=ScheduleModel, dependencies=[Depends(require_admin_role)])
async def toggle_schedule(job_id: str, payload: dict[str, Any]) -> ScheduleModel:
    enabled = payload.get('enabled')
    if not isinstance(enabled, bool):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='"enabled" boolean is required')
    try:
        job = set_job_enabled(job_id, enabled)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _to_schedule_model(job)


@router.post('/schedules/{job_id}/run', response_model=ScheduleModel, dependencies=[Depends(require_admin_role)])
async def run_schedule_now(job_id: str) -> ScheduleModel:
    try:
        job = trigger_job(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _to_schedule_model(job)

