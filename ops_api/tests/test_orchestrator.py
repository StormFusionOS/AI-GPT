"""Tests for orchestrator endpoints and Celery integration."""
from __future__ import annotations

from app.api.routes.orchestrator import dispatch_task, get_health, list_tasks
from app.models.task_runs import TaskRun
from app.schemas.orchestrator import DispatchRequest
from ops_api.orchestrator.health import run_health_checks


def _auth_dict(role: str = "SEO_ENGINEER") -> dict[str, str]:
    return {"sub": "ops@example.com", "role": role}


def test_dispatch_creates_task_run(db_session) -> None:
    request = DispatchRequest(name="serp_sample", payload={"keyword": "plumber", "locale": "en", "market": "us"})
    response = dispatch_task(request=request, claims=_auth_dict(), session=db_session)
    assert response.status == "queued"
    run = db_session.get(TaskRun, response.task_run_id)
    assert run is not None
    assert run.status in {"queued", "succeeded", "running"}


def test_dispatch_idempotency(db_session) -> None:
    payload = {"keyword": "hvac", "locale": "en", "market": "us"}
    request = DispatchRequest(name="serp_sample", payload=payload)
    first = dispatch_task(request=request, claims=_auth_dict(), session=db_session)
    second = dispatch_task(request=request, claims=_auth_dict(), session=db_session)
    assert first.status == "queued"
    assert second.status == "duplicate"
    runs = db_session.list_task_runs()
    statuses = {run.status for run in runs}
    assert "skipped" in statuses


def test_transient_failure_retries_and_succeeds(db_session) -> None:
    request = DispatchRequest(
        name="serp_sample",
        payload={"keyword": "locksmith", "locale": "en", "market": "us", "simulate": {"transient_failures": 1}},
    )
    response = dispatch_task(request=request, claims=_auth_dict(), session=db_session)
    run = db_session.get(TaskRun, response.task_run_id)
    assert run is not None
    assert run.retries >= 1
    assert run.status == "succeeded"


def test_terminal_failure_marked_failed(db_session) -> None:
    request = DispatchRequest(
        name="serp_sample",
        payload={"keyword": "roofer", "locale": "en", "market": "us", "simulate": {"fatal_error": True}},
    )
    response = dispatch_task(request=request, claims=_auth_dict(), session=db_session)
    run = db_session.get(TaskRun, response.task_run_id)
    assert run is not None
    assert run.status == "failed"


def test_health_endpoint_returns_multiple_services(db_session) -> None:
    run_health_checks()
    result = get_health(claims=_auth_dict(), session=db_session)
    assert len(result.services) >= 5
    assert all(service.status in {"ok", "warn", "down"} for service in result.services)


def test_task_listing_filters(db_session) -> None:
    payload = {"keyword": "seo", "locale": "en", "market": "us"}
    dispatch_task(request=DispatchRequest(name="serp_sample", payload=payload), claims=_auth_dict(), session=db_session)
    response = list_tasks(module="scraper", status_filter=None, claims=_auth_dict(), session=db_session)
    assert response.items


def test_dispatch_backup_task(db_session) -> None:
    request = DispatchRequest(name="backup_nightly", payload={})
    response = dispatch_task(request=request, claims=_auth_dict(), session=db_session)
    assert response.status in {"queued", "duplicate"}
