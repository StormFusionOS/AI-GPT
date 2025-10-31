"""Utilities for managing scheduled maintenance and scraping jobs."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence

from croniter import croniter  # type: ignore[import-untyped]

from app.core.config import settings


@dataclass(slots=True)
class ScheduledJob:
    """Represents a scheduled job that can be toggled or invoked manually."""

    id: str
    name: str
    cron: str
    description: str | None = None
    enabled: bool = True
    last_run: datetime | None = None
    next_run: datetime | None = None
    last_status: str | None = None

    def to_serialisable(self) -> dict[str, str | bool | None]:
        """Serialize the job into JSON compatible primitives."""

        payload = asdict(self)
        payload['last_run'] = self.last_run.isoformat() if self.last_run else None
        payload['next_run'] = self.next_run.isoformat() if self.next_run else None
        return payload

    @classmethod
    def from_payload(cls, payload: dict[str, object]) -> 'ScheduledJob':
        """Instantiate a job from persisted JSON data."""

        last_run = payload.get('last_run')
        next_run = payload.get('next_run')
        return cls(
            id=str(payload['id']),
            name=str(payload['name']),
            cron=str(payload['cron']),
            description=str(payload.get('description')) if payload.get('description') else None,
            enabled=bool(payload.get('enabled', True)),
            last_run=datetime.fromisoformat(last_run) if isinstance(last_run, str) else None,
            next_run=datetime.fromisoformat(next_run) if isinstance(next_run, str) else None,
            last_status=str(payload.get('last_status')) if payload.get('last_status') else None,
        )


STATE_PATH = Path(settings.scheduler_state_path).expanduser()


def _ensure_state_directory() -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)


def _default_jobs() -> list[ScheduledJob]:
    """Initial set of jobs used when no persisted state exists."""

    now = datetime.now(tz=UTC)
    return [
        _with_next_run(
            ScheduledJob(
                id='daily_backup',
                name='Daily Backup',
                cron='0 2 * * *',
                description='Incremental database/vector/media backup.',
            ),
            now,
        ),
        _with_next_run(
            ScheduledJob(
                id='weekly_backup_full',
                name='Weekly Full Backup',
                cron='0 3 * * 0',
                description='Full verification backup retained for long-term storage.',
            ),
            now,
        ),
        _with_next_run(
            ScheduledJob(
                id='serp_sampler',
                name='SERP Sampler',
                cron='0 */4 * * *',
                description='Capture SERP snapshots for tracked keywords.',
            ),
            now,
        ),
        _with_next_run(
            ScheduledJob(
                id='competitor_audit',
                name='Competitor Audit',
                cron='30 1 * * *',
                description='Diff competitor content for change detection.',
            ),
            now,
        ),
    ]


def _with_next_run(job: ScheduledJob, base: datetime | None = None) -> ScheduledJob:
    """Populate the next_run field using the cron schedule."""

    base_time = base or datetime.now(tz=UTC)
    try:
        iterator = croniter(job.cron, base_time)
        job.next_run = datetime.fromtimestamp(iterator.get_next(float), tz=UTC)
    except Exception:  # pragma: no cover - invalid expressions handled gracefully
        job.next_run = None
    return job


def _load_jobs() -> list[ScheduledJob]:
    if not STATE_PATH.exists():
        return _default_jobs()

    data = json.loads(STATE_PATH.read_text(encoding='utf-8'))
    jobs = [ScheduledJob.from_payload(item) for item in data]
    return jobs


def _persist_jobs(jobs: Sequence[ScheduledJob]) -> None:
    _ensure_state_directory()
    serialised = [job.to_serialisable() for job in jobs]
    STATE_PATH.write_text(json.dumps(serialised, indent=2), encoding='utf-8')


def list_jobs(*, refresh_next_run: bool = False) -> list[ScheduledJob]:
    """Return all scheduled jobs sorted by name."""

    jobs = _load_jobs()
    if refresh_next_run:
        now = datetime.now(tz=UTC)
        updated: list[ScheduledJob] = []
        for job in jobs:
            if job.enabled:
                updated.append(_with_next_run(job, now))
            else:
                job.next_run = None
                updated.append(job)
        jobs = updated
    jobs.sort(key=lambda job: job.name.lower())
    return jobs


def get_job(job_id: str) -> ScheduledJob | None:
    for job in list_jobs():
        if job.id == job_id:
            return job
    return None


def update_job(job: ScheduledJob) -> ScheduledJob:
    """Persist a modified job instance."""

    jobs = list_jobs()
    updated: list[ScheduledJob] = []
    for existing in jobs:
        if existing.id == job.id:
            updated.append(job)
        else:
            updated.append(existing)
    _persist_jobs(updated)
    return job


def set_job_enabled(job_id: str, enabled: bool) -> ScheduledJob:
    job = get_job(job_id)
    if job is None:
        raise KeyError(f'Unknown job id: {job_id}')
    job.enabled = enabled
    job = _with_next_run(job) if enabled else job
    if not enabled:
        job.next_run = None
    job.last_status = 'disabled' if not enabled else job.last_status
    return update_job(job)


def record_job_status(job_id: str, *, status: str, next_run: datetime | None = None) -> ScheduledJob:
    """Update the last run status and optionally the next run timestamp."""

    job = get_job(job_id)
    if job is None:
        raise KeyError(f'Unknown job id: {job_id}')
    job.last_run = datetime.now(tz=UTC)
    job.last_status = status
    if next_run is not None:
        job.next_run = next_run
    elif job.enabled:
        job = _with_next_run(job)
    return update_job(job)


def trigger_job(job_id: str) -> ScheduledJob:
    """Record a manual run trigger for a job."""

    job = get_job(job_id)
    if job is None:
        raise KeyError(f'Unknown job id: {job_id}')
    job.last_run = datetime.now(tz=UTC)
    job.last_status = 'queued'
    job = _with_next_run(job) if job.enabled else job
    return update_job(job)

