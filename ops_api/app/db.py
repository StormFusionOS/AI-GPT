"""Lightweight in-memory persistence for the ops API."""
from __future__ import annotations

from contextlib import contextmanager
from threading import RLock
from typing import Dict, Generator, List

from .models.alert import Alert
from .models.anomaly import Anomaly
from .models.backup_run import BackupRun
from .models.change_log import ChangeLogEntry
from .models.file_integrity import FileIntegrityRecord, IntegrityReport
from .models.service_health import ServiceHealth
from .models.suggestion import Suggestion
from .models.task_runs import TaskRun


class _Database:
    """Simple in-memory data store with coarse locking."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._task_runs: Dict[int, TaskRun] = {}
        self._service_health: Dict[int, ServiceHealth] = {}
        self._suggestions: Dict[int, Suggestion] = {}
        self._change_log: Dict[int, ChangeLogEntry] = {}
        self._anomalies: Dict[int, Anomaly] = {}
        self._file_integrity: Dict[str, FileIntegrityRecord] = {}
        self._backup_runs: Dict[int, BackupRun] = {}
        self._alerts: Dict[int, Alert] = {}
        self._service_index: Dict[str, int] = {}
        self._integrity_report: IntegrityReport | None = None
        self._task_seq = 0
        self._service_seq = 0
        self._suggestion_seq = 0
        self._change_log_seq = 0
        self._anomaly_seq = 0
        self._file_integrity_seq = 0
        self._backup_seq = 0
        self._alert_seq = 0

    def reset(self) -> None:
        with self._lock:
            self._task_runs.clear()
            self._service_health.clear()
            self._suggestions.clear()
            self._change_log.clear()
            self._anomalies.clear()
            self._file_integrity.clear()
            self._backup_runs.clear()
            self._alerts.clear()
            self._service_index.clear()
            self._integrity_report = None
            self._task_seq = 0
            self._service_seq = 0
            self._suggestion_seq = 0
            self._change_log_seq = 0
            self._anomaly_seq = 0
            self._file_integrity_seq = 0
            self._backup_seq = 0
            self._alert_seq = 0

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

    def add_suggestion(self, suggestion: Suggestion) -> Suggestion:
        with self._lock:
            if suggestion.id is None:
                self._suggestion_seq += 1
                suggestion.id = self._suggestion_seq
            self._suggestions[suggestion.id] = suggestion
            return suggestion

    def list_suggestions(self) -> List[Suggestion]:
        with self._lock:
            return list(self._suggestions.values())

    def add_change_log(self, entry: ChangeLogEntry) -> ChangeLogEntry:
        with self._lock:
            if entry.id is None:
                self._change_log_seq += 1
                entry.id = self._change_log_seq
            self._change_log[entry.id] = entry
            return entry

    def list_change_log(self) -> List[ChangeLogEntry]:
        with self._lock:
            return list(self._change_log.values())

    def add_anomaly(self, anomaly: Anomaly) -> Anomaly:
        with self._lock:
            if anomaly.id is None:
                self._anomaly_seq += 1
                anomaly.id = self._anomaly_seq
            self._anomalies[anomaly.id] = anomaly
            return anomaly

    def get_anomaly(self, anomaly_id: int) -> Anomaly | None:
        with self._lock:
            return self._anomalies.get(anomaly_id)

    def list_anomalies(self) -> List[Anomaly]:
        with self._lock:
            return list(self._anomalies.values())

    def add_service_health(self, record: ServiceHealth) -> ServiceHealth:
        with self._lock:
            if record.id is None:
                self._service_seq += 1
                record.id = self._service_seq
            self._service_health[record.id] = record
            self._service_index[record.service] = record.id
            return record

    def add_backup_run(self, run: BackupRun) -> BackupRun:
        with self._lock:
            if run.id is None:
                self._backup_seq += 1
                run.id = self._backup_seq
            self._backup_runs[run.id] = run
            return run

    def list_backup_runs(self) -> List[BackupRun]:
        with self._lock:
            return list(self._backup_runs.values())

    def add_alert(self, alert: Alert) -> Alert:
        with self._lock:
            if alert.id is None:
                self._alert_seq += 1
                alert.id = self._alert_seq
            self._alerts[alert.id] = alert
            return alert

    def list_alerts(self) -> List[Alert]:
        with self._lock:
            return list(self._alerts.values())

    def upsert_file_integrity(self, record: FileIntegrityRecord) -> FileIntegrityRecord:
        with self._lock:
            existing = self._file_integrity.get(record.path)
            if existing:
                existing.sha256 = record.sha256
                existing.scanned_at = record.scanned_at
                return existing
            if record.id is None:
                self._file_integrity_seq += 1
                record.id = self._file_integrity_seq
            self._file_integrity[record.path] = record
            return record

    def get_file_integrity(self, path: str) -> FileIntegrityRecord | None:
        with self._lock:
            return self._file_integrity.get(path)

    def list_file_integrity(self) -> List[FileIntegrityRecord]:
        with self._lock:
            return list(self._file_integrity.values())

    def set_integrity_report(self, report: IntegrityReport) -> None:
        with self._lock:
            self._integrity_report = report

    def get_integrity_report(self) -> IntegrityReport | None:
        with self._lock:
            return self._integrity_report

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

    def add(
        self,
        obj: TaskRun
        | ServiceHealth
        | Suggestion
        | ChangeLogEntry
        | Anomaly
        | FileIntegrityRecord
        | BackupRun
        | Alert,
    ) -> TaskRun | ServiceHealth | Suggestion | ChangeLogEntry | Anomaly | FileIntegrityRecord | BackupRun | Alert:
        name = obj.__class__.__name__
        if isinstance(obj, TaskRun) or name == "TaskRun":
            return self._db.add_task_run(obj)  # type: ignore[arg-type]
        if isinstance(obj, ServiceHealth) or name == "ServiceHealth":
            return self._db.add_service_health(obj)  # type: ignore[arg-type]
        if isinstance(obj, Suggestion) or name == "Suggestion":
            return self._db.add_suggestion(obj)  # type: ignore[arg-type]
        if isinstance(obj, ChangeLogEntry) or name == "ChangeLogEntry":
            return self._db.add_change_log(obj)  # type: ignore[arg-type]
        if isinstance(obj, Anomaly) or name == "Anomaly":
            return self._db.add_anomaly(obj)  # type: ignore[arg-type]
        if isinstance(obj, FileIntegrityRecord) or name == "FileIntegrityRecord":
            return self._db.upsert_file_integrity(obj)  # type: ignore[arg-type]
        if isinstance(obj, BackupRun) or name == "BackupRun":
            return self._db.add_backup_run(obj)  # type: ignore[arg-type]
        if isinstance(obj, Alert) or name == "Alert":
            return self._db.add_alert(obj)  # type: ignore[arg-type]
        raise TypeError(f"Unsupported object type: {type(obj)}")

    def get(
        self,
        model: type[TaskRun]
        | type[ServiceHealth]
        | type[Suggestion]
        | type[ChangeLogEntry]
        | type[Anomaly]
        | type[BackupRun]
        | type[Alert],
        identifier: int,
    ) -> TaskRun | ServiceHealth | Suggestion | ChangeLogEntry | Anomaly | BackupRun | Alert | None:
        name = getattr(model, "__name__", "")
        if model is TaskRun or name == "TaskRun":
            return self._db.get_task_run(identifier)
        if model is ServiceHealth or name == "ServiceHealth":
            return self._db.get_service_health(identifier)
        if model is Suggestion or name == "Suggestion":
            return next((item for item in self._db.list_suggestions() if item.id == identifier), None)
        if model is ChangeLogEntry or name == "ChangeLogEntry":
            return next((item for item in self._db.list_change_log() if item.id == identifier), None)
        if model is Anomaly or name == "Anomaly":
            return self._db.get_anomaly(identifier)
        if model is BackupRun or name == "BackupRun":
            return next((item for item in self._db.list_backup_runs() if item.id == identifier), None)
        if model is Alert or name == "Alert":
            return next((item for item in self._db.list_alerts() if item.id == identifier), None)
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

    def list_suggestions(self) -> List[Suggestion]:
        return sorted(self._db.list_suggestions(), key=lambda suggestion: suggestion.created_at, reverse=True)

    def list_change_log(self) -> List[ChangeLogEntry]:
        return sorted(self._db.list_change_log(), key=lambda entry: entry.created_at, reverse=True)

    def list_anomalies(self) -> List[Anomaly]:
        return sorted(self._db.list_anomalies(), key=lambda anomaly: anomaly.created_at, reverse=True)

    def list_file_integrity(self) -> List[FileIntegrityRecord]:
        return sorted(self._db.list_file_integrity(), key=lambda record: record.path)

    def get_file_integrity(self, path: str) -> FileIntegrityRecord | None:
        return self._db.get_file_integrity(path)

    def list_backup_runs(self) -> List[BackupRun]:
        return sorted(self._db.list_backup_runs(), key=lambda run: run.started_at, reverse=True)

    def list_alerts(self) -> List[Alert]:
        return sorted(self._db.list_alerts(), key=lambda alert: alert.created_at, reverse=True)

    def set_integrity_report(self, report: IntegrityReport) -> None:
        self._db.set_integrity_report(report)

    def get_integrity_report(self) -> IntegrityReport | None:
        return self._db.get_integrity_report()

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
