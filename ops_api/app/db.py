"""Lightweight in-memory persistence for the ops API."""
from __future__ import annotations

from contextlib import contextmanager
from threading import RLock
from typing import Dict, Generator, List

from .models.service_health import ServiceHealth
from .models.task_runs import TaskRun


class _Database:
    """Simple in-memory data store with coarse locking."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._task_runs: Dict[int, TaskRun] = {}
        self._service_health: Dict[int, ServiceHealth] = {}
        self._service_index: Dict[str, int] = {}
        self._task_seq = 0
        self._service_seq = 0

    def reset(self) -> None:
        with self._lock:
            self._task_runs.clear()
            self._service_health.clear()
            self._service_index.clear()
            self._task_seq = 0
            self._service_seq = 0

    def add_task_run(self, run: TaskRun) -> TaskRun:
        with self._lock:
            if run.id is None:
                self._task_seq += 1
                run.id = self._task_seq
            self._task_runs[run.id] = run
            return run

    def get_task_run(self, run_id: int) -> TaskRun | None:
        with self._lock:
            return self._task_runs.get(run_id)

    def list_task_runs(self) -> List[TaskRun]:
        with self._lock:
            return list(self._task_runs.values())

    def add_service_health(self, record: ServiceHealth) -> ServiceHealth:
        with self._lock:
            if record.id is None:
                self._service_seq += 1
                record.id = self._service_seq
            self._service_health[record.id] = record
            self._service_index[record.service] = record.id
            return record

    def get_service_health(self, record_id: int) -> ServiceHealth | None:
        with self._lock:
            return self._service_health.get(record_id)

    def get_service_health_by_name(self, service: str) -> ServiceHealth | None:
        with self._lock:
            record_id = self._service_index.get(service)
            return self._service_health.get(record_id) if record_id is not None else None

    def list_service_health(self) -> List[ServiceHealth]:
        with self._lock:
            return list(self._service_health.values())


_database = _Database()


class DatabaseSession:
    """Session wrapper used by FastAPI dependencies and Celery hooks."""

    def __init__(self, database: _Database) -> None:
        self._db = database
        self._closed = False

    def add(self, obj: TaskRun | ServiceHealth) -> TaskRun | ServiceHealth:
        if isinstance(obj, TaskRun):
            return self._db.add_task_run(obj)
        if isinstance(obj, ServiceHealth):
            return self._db.add_service_health(obj)
        raise TypeError(f"Unsupported object type: {type(obj)}")

    def get(self, model: type[TaskRun] | type[ServiceHealth], identifier: int) -> TaskRun | ServiceHealth | None:
        if model is TaskRun:
            return self._db.get_task_run(identifier)
        if model is ServiceHealth:
            return self._db.get_service_health(identifier)
        raise TypeError("Unsupported model class")

    def list_task_runs(self, *, module: str | None = None, status: str | None = None, limit: int | None = None) -> List[TaskRun]:
        runs = sorted(self._db.list_task_runs(), key=lambda run: run.queued_at, reverse=True)
        if module:
            runs = [run for run in runs if run.module == module]
        if status:
            runs = [run for run in runs if run.status == status]
        if limit is not None:
            runs = runs[:limit]
        return runs

    def list_service_health(self) -> List[ServiceHealth]:
        return sorted(self._db.list_service_health(), key=lambda record: record.service)

    def get_service_health_by_name(self, service: str) -> ServiceHealth | None:
        return self._db.get_service_health_by_name(service)

    def commit(self) -> None:  # pragma: no cover - maintained for API compatibility
        return None

    def rollback(self) -> None:  # pragma: no cover - maintained for API compatibility
        return None

    def flush(self) -> None:  # pragma: no cover - compatibility shim
        return None

    def close(self) -> None:
        self._closed = True


def get_database() -> _Database:
    return _database


@contextmanager
def session_scope() -> Generator[DatabaseSession, None, None]:
    session = DatabaseSession(_database)
    try:
        yield session
    finally:
        session.close()


def get_session() -> Generator[DatabaseSession, None, None]:
    session = DatabaseSession(_database)
    try:
        yield session
    finally:
        session.close()


def reset_database() -> None:
    _database.reset()


def init_db() -> None:  # pragma: no cover - compatibility shim
    """Provided for compatibility with startup hooks."""
    return None
