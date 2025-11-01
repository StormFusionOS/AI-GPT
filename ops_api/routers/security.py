"""Security hygiene endpoints for the ops console."""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends

from ops_api.app.api.deps import get_claims, get_db
from ops_api.app.db import DatabaseSession
from ops_api.app.schemas.security import (
    SecurityHygieneResponse,
    SecurityScanResponse,
    make_drift_view,
    make_record_view,
)
from ops_api.app.security import RoleGuard
from ops_api.security.integrity import IntegrityScanner

ALLOWED_ROLES = RoleGuard(["SEO_ENGINEER", "DEVOPS", "OWNER"])

router = APIRouter(prefix="/security", tags=["security"])


def _authorise(claims: Dict[str, Any]) -> None:
    ALLOWED_ROLES(claims)


def _build_response(session: DatabaseSession, report) -> SecurityHygieneResponse:
    records = [make_record_view(record) for record in session.list_file_integrity()]
    drift = [make_drift_view(item) for item in report.drift]
    return SecurityHygieneResponse(last_scan=report.generated_at, records=records, drift=drift)


@router.get("/hygiene", response_model=SecurityHygieneResponse)
def get_security_hygiene(
    claims: Dict[str, Any] = Depends(get_claims),
    session: DatabaseSession = Depends(get_db),
) -> SecurityHygieneResponse:
    _authorise(claims)
    scanner = IntegrityScanner()
    report = scanner.status(session)
    return _build_response(session, report)


@router.post("/scan", response_model=SecurityScanResponse)
def run_security_scan(
    claims: Dict[str, Any] = Depends(get_claims),
    session: DatabaseSession = Depends(get_db),
) -> SecurityScanResponse:
    _authorise(claims)
    scanner = IntegrityScanner()
    report = scanner.scan(session)
    response = _build_response(session, report)
    return SecurityScanResponse(**response.dict())
