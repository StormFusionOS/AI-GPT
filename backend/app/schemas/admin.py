"""Schemas supporting admin review, audit, and AI prompt tooling."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ReviewChangeModel(BaseModel):
    """Represents an AI suggested change awaiting human review."""

    id: str
    title: str
    module: str
    change_type: str = Field(alias='changeType')
    status: Literal['pending', 'approved', 'rejected', 'applied']
    created_at: datetime = Field(alias='createdAt')
    submitted_by: str = Field(alias='submittedBy')
    summary: str
    content_id: str = Field(alias='contentId')
    current_version_id: str = Field(alias='currentVersionId')
    proposed_version_id: str = Field(alias='proposedVersionId')
    last_reviewed_at: datetime | None = Field(default=None, alias='lastReviewedAt')
    last_reviewed_by: str | None = Field(default=None, alias='lastReviewedBy')
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReviewActionRequest(BaseModel):
    """Payload for approving or rejecting a change log entry."""

    note: str | None = None


class ContentVersionModel(BaseModel):
    """Individual version of a content blob tracked for diffs."""

    id: str
    label: str
    author: str
    created_at: datetime = Field(alias='createdAt')
    content: str


class DiffResponseModel(BaseModel):
    """Response for diff requests including both content versions."""

    content_id: str = Field(alias='contentId')
    version_a: ContentVersionModel = Field(alias='versionA')
    version_b: ContentVersionModel = Field(alias='versionB')


class AuditIssueModel(BaseModel):
    """Single audit issue returned for a page."""

    id: str
    description: str
    severity: Literal['low', 'medium', 'high', 'critical']
    resolved: bool
    recommendation: str | None = None


class AuditSummaryModel(BaseModel):
    """Overview row for SEO audits table."""

    id: str
    url: str
    audit_date: datetime = Field(alias='auditDate')
    score: int
    issue_count: int = Field(alias='issueCount')
    trend: Literal['improving', 'steady', 'declining']
    top_severity: Literal['low', 'medium', 'high', 'critical'] = Field(alias='topSeverity')


class AuditDetailModel(BaseModel):
    """Detailed audit response including issues."""

    id: str
    url: str
    audit_date: datetime = Field(alias='auditDate')
    score: int
    summary: str
    issues: list[AuditIssueModel]


class PromptDefinitionModel(BaseModel):
    """Descriptor for available prompt templates."""

    name: str
    label: str
    description: str
    input_schema: dict[str, Any] = Field(alias='inputSchema')


class PromptRunRequest(BaseModel):
    """Request payload when manually executing a prompt."""

    prompt: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class PromptRunResponse(BaseModel):
    """Response with rendered prompt output."""

    prompt: str
    executed_at: datetime = Field(alias='executedAt')
    output: Any
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    'ReviewChangeModel',
    'ReviewActionRequest',
    'ContentVersionModel',
    'DiffResponseModel',
    'AuditIssueModel',
    'AuditSummaryModel',
    'AuditDetailModel',
    'PromptDefinitionModel',
    'PromptRunRequest',
    'PromptRunResponse',
]
