"""File integrity monitoring utilities."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable, Mapping


@dataclass(slots=True)
class IntegrityRecord:
    """Describes the stored checksum metadata for a watched file."""

    path: str
    checksum: str
    updated_at: datetime

    def to_payload(self) -> dict[str, str]:
        return {
            'path': self.path,
            'checksum': self.checksum,
            'updated_at': self.updated_at.isoformat(),
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, str]) -> 'IntegrityRecord':
        return cls(
            path=payload['path'],
            checksum=payload['checksum'],
            updated_at=datetime.fromisoformat(payload['updated_at']),
        )


@dataclass(slots=True)
class IntegrityIssue:
    """Represents a deviation detected during an integrity scan."""

    path: str
    status: str
    message: str
    observed_at: datetime

    def to_payload(self) -> dict[str, str]:
        return {
            'path': self.path,
            'status': self.status,
            'message': self.message,
            'observed_at': self.observed_at.isoformat(),
        }


class IntegrityMonitor:
    """Compute and validate file hashes for tamper detection."""

    def __init__(self, *, watch_paths: Iterable[str], state_file: str) -> None:
        self.watch_paths = [Path(path).expanduser().resolve() for path in watch_paths]
        self.state_path = Path(state_file).expanduser()
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_state(self) -> dict[str, IntegrityRecord]:
        if not self.state_path.exists():
            return {}
        payload = json.loads(self.state_path.read_text(encoding='utf-8'))
        records: dict[str, IntegrityRecord] = {}
        for entry in payload:
            record = IntegrityRecord.from_payload(entry)
            records[record.path] = record
        return records

    def _save_state(self, records: dict[str, IntegrityRecord]) -> None:
        serialised = [record.to_payload() for record in records.values()]
        self.state_path.write_text(json.dumps(serialised, indent=2), encoding='utf-8')

    @staticmethod
    def _hash_file(path: Path) -> str:
        hasher = hashlib.sha256()
        with path.open('rb') as file_handle:
            for chunk in iter(lambda: file_handle.read(65536), b''):
                hasher.update(chunk)
        return hasher.hexdigest()

    def scan(self, *, update_baseline: bool = False) -> tuple[list[IntegrityIssue], dict[str, IntegrityRecord]]:
        """Scan watched files and optionally refresh the stored baseline."""

        records = self._load_state()
        findings: list[IntegrityIssue] = []
        now = datetime.now(tz=UTC)

        observed: dict[str, IntegrityRecord] = {}
        for path in self.watch_paths:
            if not path.exists():
                findings.append(
                    IntegrityIssue(
                        path=str(path),
                        status='missing',
                        message='File missing during integrity scan',
                        observed_at=now,
                    )
                )
                continue

            checksum = self._hash_file(path)
            record = IntegrityRecord(path=str(path), checksum=checksum, updated_at=now)
            observed[str(path)] = record

            previous = records.get(str(path))
            if previous is None:
                findings.append(
                    IntegrityIssue(
                        path=str(path),
                        status='new',
                        message='File not present in baseline; storing new checksum',
                        observed_at=now,
                    )
                )
            elif previous.checksum != checksum:
                findings.append(
                    IntegrityIssue(
                        path=str(path),
                        status='changed',
                        message='Checksum differs from baseline',
                        observed_at=now,
                    )
                )

        # Detect stale baseline entries
        for path, record in records.items():
            if path not in observed:
                findings.append(
                    IntegrityIssue(
                        path=path,
                        status='removed',
                        message='File previously tracked but missing from watch list',
                        observed_at=now,
                    )
                )

        if update_baseline:
            self._save_state(observed)

        return findings, observed

    def refresh_baseline(self) -> None:
        """Force a baseline refresh, storing current checksums."""

        _, observed = self.scan(update_baseline=True)
        self._save_state(observed)

