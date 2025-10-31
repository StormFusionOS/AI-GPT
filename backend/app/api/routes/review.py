"""Endpoints for managing AI review queue and diff retrieval."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.deps import require_admin_role
from app.schemas import (
    DiffResponseModel,
    ReviewActionRequest,
    ReviewChangeModel,
)
from app.services import review_queue


def _to_model(change: review_queue.ReviewChange) -> ReviewChangeModel:
    return ReviewChangeModel(
        id=change.id,
        title=change.title,
        module=change.module,
        changeType=change.change_type,
        status=change.status,
        createdAt=change.created_at,
        submittedBy=change.submitted_by,
        summary=change.summary,
        contentId=change.content_id,
        currentVersionId=change.current_version_id,
        proposedVersionId=change.proposed_version_id,
        lastReviewedAt=change.last_reviewed_at,
        lastReviewedBy=change.last_reviewed_by,
        metadata=change.metadata,
    )

router = APIRouter(prefix='/review-queue', tags=['review'], dependencies=[Depends(require_admin_role)])


@router.get('', response_model=list[ReviewChangeModel])
async def list_review_changes(status: str | None = Query(default=None)) -> list[ReviewChangeModel]:
    """Return review queue items filtered by optional status."""

    return [_to_model(item) for item in review_queue.list_changes(status)]


@router.get('/{change_id}', response_model=ReviewChangeModel)
async def get_review_change(change_id: str) -> ReviewChangeModel:
    change = review_queue.get_change(change_id)
    return _to_model(change)


@router.post('/{change_id}/approve', response_model=ReviewChangeModel, status_code=status.HTTP_200_OK)
async def approve_change(change_id: str, request: Request, payload: ReviewActionRequest | None = None) -> ReviewChangeModel:
    """Approve an AI suggestion and record the actor."""

    actor = request.headers.get('X-Admin-Email', 'admin@example.com')
    note = payload.note if payload else None
    change = review_queue.update_change_status(change_id, 'approved', actor, note)
    return _to_model(change)


@router.post('/{change_id}/reject', response_model=ReviewChangeModel, status_code=status.HTTP_200_OK)
async def reject_change(change_id: str, request: Request, payload: ReviewActionRequest | None = None) -> ReviewChangeModel:
    actor = request.headers.get('X-Admin-Email', 'admin@example.com')
    note = payload.note if payload else None
    change = review_queue.update_change_status(change_id, 'rejected', actor, note)
    return _to_model(change)


@router.get('/diff', response_model=DiffResponseModel)
async def get_content_diff(
    content_id: str = Query(alias='contentId'),
    version_a: str = Query(alias='version1'),
    version_b: str = Query(alias='version2'),
) -> DiffResponseModel:
    """Return the raw content for two versions so the UI can render a diff."""

    version_left, version_right = review_queue.resolve_diff(content_id, version_a, version_b)

    return DiffResponseModel(
        contentId=content_id,
        versionA={
            'id': version_left.id,
            'label': version_left.label,
            'author': version_left.author,
            'createdAt': version_left.created_at,
            'content': version_left.body,
        },
        versionB={
            'id': version_right.id,
            'label': version_right.label,
            'author': version_right.author,
            'createdAt': version_right.created_at,
            'content': version_right.body,
        },
    )


__all__ = ['router']
