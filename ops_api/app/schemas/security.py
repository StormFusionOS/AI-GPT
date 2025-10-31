"""Pydantic schemas for security hygiene endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from ..models.file_integrity import FileIntegrityRecord, IntegrityDrift


class IntegrityRecordView(BaseModel):
    path: str
    sha256: str
    scanned_at: datetime


class IntegrityDriftView(BaseModel):
    path: str
    expected_sha: Optional[str]
    observed_sha: Optional[str]
    reason: str


class SecurityHygieneResponse(BaseModel):
    last_scan: Optional[datetime]
    records: List[IntegrityRecordView]
    drift: List[IntegrityDriftView]


class SecurityScanResponse(SecurityHygieneResponse):
    pass


def make_record_view(record: FileIntegrityRecord) -> IntegrityRecordView:
    return IntegrityRecordView(path=record.path, sha256=record.sha256, scanned_at=record.scanned_at)


def make_drift_view(drift: IntegrityDrift) -> IntegrityDriftView:
    return IntegrityDriftView(
        path=drift.path,
        expected_sha=drift.expected_sha,
        observed_sha=drift.observed_sha,
        reason=drift.reason,
    )
