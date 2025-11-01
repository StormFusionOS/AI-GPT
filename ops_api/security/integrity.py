"""Integrity scanning utilities for ops platform hardening."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

from ops_api.app.core import config as config_module
from ops_api.app.db import DatabaseSession
from ops_api.app.models.file_integrity import (
    FileIntegrityRecord,
    IntegrityDrift,
    IntegrityReport,
)


class IntegrityScanner:
    """Computes directory hashes and records drift information."""

    def __init__(self, *, targets: Iterable[str] | None = None) -> None:
        settings = config_module.get_settings()
        configured = targets if targets is not None else settings.integrity_paths or []
        resolved: List[Path] = []
        for entry in configured:
            if not entry:
                continue
            resolved.append(Path(entry).expanduser().resolve())
        self.targets = resolved

    @staticmethod
    def _hash_path(path: Path) -> str | None:
        if not path.exists():
            return None
        digest = hashlib.sha256()
        if path.is_file():
            digest.update(path.name.encode("utf-8"))
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(8192), b""):
                    digest.update(chunk)
            return digest.hexdigest()
        files = [item for item in path.rglob("*") if item.is_file()]
        if not files:
            digest.update(path.name.encode("utf-8"))
        for file_path in sorted(files):
            digest.update(str(file_path.relative_to(path)).encode("utf-8"))
            with file_path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(8192), b""):
                    digest.update(chunk)
        return digest.hexdigest()

    def scan(self, session: DatabaseSession) -> IntegrityReport:
        """Run a scan and persist baseline information."""

        drifts: List[IntegrityDrift] = []
        for target in self.targets:
            observed = self._hash_path(target)
            record = session.get_file_integrity(str(target))
            now = datetime.now(timezone.utc)
            if record is None:
                record = FileIntegrityRecord(path=str(target), sha256=observed or "", scanned_at=now)
                session.add(record)
                if observed is None:
                    drifts.append(
                        IntegrityDrift(
                            path=str(target),
                            expected_sha=None,
                            observed_sha=None,
                            reason="missing",
                        )
                    )
                continue
            record.touch()
            if observed is None:
                drifts.append(
                    IntegrityDrift(
                        path=str(target),
                        expected_sha=record.sha256,
                        observed_sha=None,
                        reason="missing",
                    )
                )
                continue
            if record.sha256 != observed:
                drifts.append(
                    IntegrityDrift(
                        path=str(target),
                        expected_sha=record.sha256,
                        observed_sha=observed,
                        reason="hash_mismatch",
                    )
                )
            record.sha256 = observed
            session.add(record)
        report = IntegrityReport(generated_at=datetime.now(timezone.utc), drift=drifts)
        session.set_integrity_report(report)
        return report

    def status(self, session: DatabaseSession) -> IntegrityReport:
        """Return the last report or an empty snapshot if no scans were run."""

        existing = session.get_integrity_report()
        if existing is not None:
            return existing
        report = IntegrityReport(generated_at=datetime.now(timezone.utc), drift=[])
        session.set_integrity_report(report)
        return report
