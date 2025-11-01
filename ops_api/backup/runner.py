"""Backup orchestration utilities for the ops service."""
from __future__ import annotations

import gzip
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterable, Sequence
from urllib.parse import urlparse, urlunparse

from app.core.config import get_settings
from app.db import session_scope
from app.models import Alert, BackupRun


class CommandExecutor:
    """Wrapper around :func:`subprocess.run` to aid testing."""

    def run(self, args: Sequence[str], **kwargs) -> subprocess.CompletedProcess[bytes]:
        kwargs.setdefault("check", True)
        return subprocess.run(args, **kwargs)


def _checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_manifest(directory: Path, files: Iterable[Path]) -> Path:
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "files": [
            {"name": file.name, "bytes": file.stat().st_size, "sha256": _checksum(file)}
            for file in files
        ],
    }
    manifest_path = directory / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def _pg_restore_list(executor: CommandExecutor, gz_path: Path) -> None:
    with gzip.open(gz_path, "rb") as handle:
        data = handle.read()
    executor.run(["pg_restore", "-l"], input=data)


def _dump_database(name: str, dsn: str, dest_dir: Path, executor: CommandExecutor) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    temp_path = dest_dir / f"{name}.dump"
    executor.run(["pg_dump", "--dbname", dsn, "--format=custom", f"--file={temp_path}"])
    executor.run(["pg_restore", "-l", str(temp_path)])
    gz_path = dest_dir / f"{name}.sql.gz"
    with temp_path.open("rb") as src, gzip.open(gz_path, "wb") as dst:
        shutil.copyfileobj(src, dst)
    temp_path.unlink(missing_ok=True)
    _pg_restore_list(executor, gz_path)
    return gz_path


def _sync_to_nas(source_dir: Path, destination: str, binary: str, executor: CommandExecutor) -> None:
    if not destination:
        return
    if binary == "rclone":
        executor.run([binary, "copy", str(source_dir), destination])
    else:
        executor.run([binary, "-a", f"{source_dir}/", destination])


def _create_alert(message: str) -> None:
    with session_scope() as session:
        session.add(Alert(level="CRITICAL", message=message))


def _record_run(run: BackupRun) -> BackupRun:
    with session_scope() as session:
        session.add(run)
    return run


def _latest_backup_directory(root: Path) -> Path | None:
    if not root.exists():
        return None
    directories = [path for path in root.iterdir() if path.is_dir()]
    if not directories:
        return None
    return sorted(directories)[-1]


def _database_dsn_with(db_dsn: str, database_name: str) -> str:
    parsed = urlparse(db_dsn)
    path = f"/{database_name}"
    return urlunparse(parsed._replace(path=path))


def run_nightly_backup(executor: CommandExecutor | None = None) -> BackupRun:
    settings = get_settings()
    executor = executor or CommandExecutor()
    today = datetime.now(timezone.utc)
    target_dir = (settings.backup_root / "db" / today.strftime("%Y%m%d")).resolve()  # type: ignore[operator]
    run = BackupRun(run_type="nightly", location=str(target_dir))
    _record_run(run)
    try:
        ops_dump = _dump_database("ops", settings.ops_pg_dsn, target_dir, executor)
        crm_dump = _dump_database("crm", settings.crm_pg_dsn, target_dir, executor)
        manifest = _write_manifest(target_dir, [ops_dump, crm_dump])
        total_bytes = ops_dump.stat().st_size + crm_dump.stat().st_size + manifest.stat().st_size
        run.bytes = total_bytes
        run.verify_ok = True
        if settings.backup_nas_path:
            _sync_to_nas(target_dir, settings.backup_nas_path, settings.backup_sync_binary, executor)
    except Exception as exc:  # pragma: no cover - exercised in tests via expected failure path
        run.mark_finished(ok=False, verify_ok=False, message=str(exc))
        _create_alert(f"Nightly backup failed: {exc}")
        raise
    else:
        run.mark_finished(ok=True, verify_ok=True, message="Nightly backup completed")
    return run


def verify_latest_backup(executor: CommandExecutor | None = None) -> BackupRun:
    settings = get_settings()
    executor = executor or CommandExecutor()
    backup_root = (settings.backup_root / "db").resolve()  # type: ignore[operator]
    latest = _latest_backup_directory(backup_root)
    if latest is None:
        raise RuntimeError("No backups available for verification")
    run = BackupRun(run_type="verify", location=str(latest), verify_ok=True)
    _record_run(run)
    manifest_path = latest / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        mismatches: list[str] = []
        for entry in manifest.get("files", []):
            file_path = latest / entry["name"]
            expected = entry["sha256"]
            if not file_path.exists():
                mismatches.append(f"Missing file {file_path.name}")
                continue
            current = _checksum(file_path)
            if current != expected:
                mismatches.append(f"Checksum mismatch for {file_path.name}")
            else:
                _pg_restore_list(executor, file_path)
        if mismatches:
            raise RuntimeError("; ".join(mismatches))
    except Exception as exc:
        run.mark_finished(ok=False, verify_ok=False, message=str(exc))
        _create_alert(f"Backup verification failed: {exc}")
        raise
    else:
        bytes_total = sum((latest / entry["name"]).stat().st_size for entry in manifest.get("files", []))
        run.bytes = bytes_total
        run.mark_finished(ok=True, verify_ok=True, message="Verification successful")
    return run


def disaster_recovery_test(executor: CommandExecutor | None = None) -> BackupRun:
    settings = get_settings()
    executor = executor or CommandExecutor()
    backup_root = (settings.backup_root / "db").resolve()  # type: ignore[operator]
    latest = _latest_backup_directory(backup_root)
    if latest is None:
        raise RuntimeError("No backups available for DR test")
    ops_dump = latest / "ops.sql.gz"
    if not ops_dump.exists():
        raise RuntimeError("Ops backup not found for DR test")
    run = BackupRun(run_type="dr_test", location=str(latest), verify_ok=None)
    _record_run(run)
    temp_db = f"ops_dr_{int(datetime.now(timezone.utc).timestamp())}"
    admin_dsn = settings.ops_pg_admin_dsn or settings.ops_pg_dsn
    temp_dsn = _database_dsn_with(admin_dsn, temp_db)
    with NamedTemporaryFile(suffix=".dump", delete=False) as temp_dump:
        with gzip.open(ops_dump, "rb") as source:
            shutil.copyfileobj(source, temp_dump)
        temp_dump_path = Path(temp_dump.name)
    try:
        executor.run(["psql", admin_dsn, "-c", f"CREATE DATABASE {temp_db}"])
        executor.run(["pg_restore", f"--dbname={temp_dsn}", str(temp_dump_path)])
        executor.run(["psql", temp_dsn, "-c", "SELECT 1"])
    except Exception as exc:
        run.mark_finished(ok=False, verify_ok=False, message=str(exc))
        _create_alert(f"DR test failed: {exc}")
        raise
    finally:
        try:
            executor.run(["psql", admin_dsn, "-c", f"DROP DATABASE IF EXISTS {temp_db}"])
        except Exception:
            pass
        temp_dump_path.unlink(missing_ok=True)
    run.bytes = ops_dump.stat().st_size
    run.mark_finished(ok=True, verify_ok=True, message="DR test succeeded")
    return run


__all__ = [
    "CommandExecutor",
    "run_nightly_backup",
    "verify_latest_backup",
    "disaster_recovery_test",
]
