"""SEO audit endpoints used by the admin interface."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import require_admin_role
from app.schemas import AuditDetailModel, AuditSummaryModel
from app.services import seo_audit

router = APIRouter(prefix='/seo', tags=['seo'], dependencies=[Depends(require_admin_role)])


_SEVERITY_RANK = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}


@router.get('/audits', response_model=list[AuditSummaryModel])
async def list_audits(
    severity: str | None = Query(default=None),
    search: str | None = Query(default=None),
) -> list[AuditSummaryModel]:
    records = seo_audit.list_audits(severity=severity, search=search)
    return [
        AuditSummaryModel(
            id=record.id,
            url=record.url,
            auditDate=record.audit_date,
            score=record.score,
            issueCount=len([issue for issue in record.issues if not issue.resolved]),
            trend=record.trend,  # type: ignore[arg-type]
            topSeverity=(
                max((issue.severity for issue in record.issues), key=lambda sev: _SEVERITY_RANK.get(sev, 0))
                if record.issues
                else 'low'
            ),
        )
        for record in records
    ]


@router.get('/audits/{audit_id}', response_model=AuditDetailModel)
async def get_audit(audit_id: str) -> AuditDetailModel:
    record = seo_audit.get_audit(audit_id)
    return AuditDetailModel(
        id=record.id,
        url=record.url,
        auditDate=record.audit_date,
        score=record.score,
        summary=record.summary,
        issues=[
            {
                'id': issue.id,
                'description': issue.description,
                'severity': issue.severity,
                'resolved': issue.resolved,
                'recommendation': issue.recommendation,
            }
            for issue in record.issues
        ],
    )


__all__ = ['router']
