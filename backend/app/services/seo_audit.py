"""Mock SEO audit data helpers for the admin console."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Dict, List

from fastapi import HTTPException


@dataclass
class AuditIssue:
    id: str
    description: str
    severity: str
    resolved: bool
    recommendation: str | None


@dataclass
class AuditRecord:
    id: str
    url: str
    audit_date: datetime
    score: int
    summary: str
    trend: str
    issues: List[AuditIssue]


_NOW = datetime.now(tz=UTC)

_AUDITS: Dict[str, AuditRecord] = {
    'audit-200': AuditRecord(
        id='audit-200',
        url='https://rivercityclean.com/',
        audit_date=_NOW - timedelta(days=2, hours=4),
        score=82,
        summary='Homepage healthy but missing updated schema telephone reference.',
        trend='steady',
        issues=[
            AuditIssue(
                id='issue-500',
                description='LocalBusiness schema missing telephone property.',
                severity='medium',
                resolved=False,
                recommendation='Accept schema enhancement from review queue to include contact number.',
            ),
            AuditIssue(
                id='issue-501',
                description='Hero image missing descriptive alt text.',
                severity='low',
                resolved=False,
                recommendation='Add descriptive alt text matching new hero copy.',
            ),
        ],
    ),
    'audit-201': AuditRecord(
        id='audit-201',
        url='https://rivercityclean.com/services/warehouse-cleaning',
        audit_date=_NOW - timedelta(days=5, hours=3),
        score=68,
        summary='Competitor outranking due to fresher content and FAQ coverage.',
        trend='declining',
        issues=[
            AuditIssue(
                id='issue-510',
                description='Content freshness lagging competitors by ~6 months.',
                severity='high',
                resolved=False,
                recommendation='Run content refresher workflow and publish updated case studies.',
            ),
            AuditIssue(
                id='issue-511',
                description='No FAQ schema present on service page.',
                severity='medium',
                resolved=False,
                recommendation='Generate targeted FAQs covering logistics, pricing, and turnaround time.',
            ),
        ],
    ),
    'audit-202': AuditRecord(
        id='audit-202',
        url='https://rivercityclean.com/blog/eco-friendly-products',
        audit_date=_NOW - timedelta(days=10),
        score=91,
        summary='Content fully optimized after March refresh cycle.',
        trend='improving',
        issues=[
            AuditIssue(
                id='issue-520',
                description='Structured data validation warnings resolved.',
                severity='low',
                resolved=True,
                recommendation=None,
            ),
        ],
    ),
}


def list_audits(*, severity: str | None = None, search: str | None = None) -> List[AuditRecord]:
    """Return audits sorted by most recent run with optional filtering."""

    items = list(_AUDITS.values())

    if severity:
        target = severity.lower()
        items = [
            record
            for record in items
            if any(issue.severity.lower() == target for issue in record.issues)
        ]

    if search:
        lowered = search.lower()
        items = [record for record in items if lowered in record.url.lower()]

    items.sort(key=lambda record: record.audit_date, reverse=True)
    return items


def get_audit(audit_id: str) -> AuditRecord:
    if audit_id not in _AUDITS:
        raise HTTPException(status_code=404, detail='Audit not found')
    return _AUDITS[audit_id]


__all__ = ['list_audits', 'get_audit', 'AuditRecord', 'AuditIssue']
