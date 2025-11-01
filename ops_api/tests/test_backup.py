"""Tests for backup orchestration utilities."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

import pytest

from app.db import session_scope
from ops_api.backup import runner
from ops_api.backup.runner import disaster_recovery_test, run_nightly_backup, verify_latest_backup


class DummyProcess:
    def __init__(self, args: Sequence[str]) -> None:
        self.args = args
        self.returncode = 0


@pytest.fixture(autouse=True)
def _isolate_commands(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(args: Sequence[str], **kwargs: Any) -> DummyProcess:
        cmd = args[0]
        if cmd == "pg_dump":
            file_arg = next((part for part in args if str(part).startswith("--file=")), None)
            if file_arg is None:
                raise AssertionError("pg_dump missing --file")
            dump_path = Path(str(file_arg).split("=", 1)[1])
            dump_path.parent.mkdir(parents=True, exist_ok=True)
            dump_path.write_bytes(b"PGDUMP")
        return DummyProcess(args)

    monkeypatch.setattr(runner.subprocess, "run", fake_run)  # type: ignore[attr-defined]
    yield


def _latest_backup_dir() -> Path:
    with session_scope() as session:
        runs = session.list_backup_runs()
    assert runs
    return Path(runs[0].location)


def test_nightly_backup_records_run() -> None:
    run = run_nightly_backup()
    assert run.ok
    assert run.verify_ok
    with session_scope() as session:
        stored = session.list_backup_runs()
    assert stored and stored[0].run_type == "nightly"
    manifest = Path(stored[0].location) / "manifest.json"
    assert manifest.exists()
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert len(data.get("files", [])) == 2


def test_verify_detects_corruption(monkeypatch: pytest.MonkeyPatch) -> None:
    run_nightly_backup()
    backup_dir = _latest_backup_dir()
    ops_backup = backup_dir / "ops.sql.gz"
    ops_backup.write_bytes(b"corrupted")
    with pytest.raises(RuntimeError):
        verify_latest_backup()
    with session_scope() as session:
        runs = session.list_backup_runs()
        assert any(r.run_type == "verify" and not r.verify_ok for r in runs)
        alerts = session.list_alerts()
        assert any("verification" in alert.message for alert in alerts)


def test_disaster_recovery_records_run() -> None:
    run_nightly_backup()
    result = disaster_recovery_test()
    assert result.ok
    with session_scope() as session:
        runs = session.list_backup_runs()
    assert any(r.run_type == "dr_test" for r in runs)
