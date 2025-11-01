"""Review queue endpoints for SEO suggestions."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_db, get_wordpress, require_ops_claims
from app.db import DatabaseSession
from app.models import ChangeLogEntry, Suggestion
from app.schemas.review import (
    ChangeLogInfo,
    ReviewActionResponse,
    ReviewDecisionRequest,
    SuggestionListResponse,
    SuggestionRecord,
)
from app.services.wordpress import WordPressSite

router = APIRouter(prefix="/review", tags=["review"])

_VALID_TYPES = {"meta", "faq", "jsonld", "link", "snippet"}
_VALID_STATUS = {"pending", "approved", "rejected", "executed"}


def _authorise(claims: Dict[str, Any]) -> str:
    # claims already validated by require_ops_claims
    return str(claims.get("sub", "unknown"))


def _current_state(suggestion: Suggestion, site: WordPressSite) -> Dict[str, Any]:
    page_id = suggestion.target
    if suggestion.type == "meta":
        return {"meta": site.get_meta(page_id)}
    if suggestion.type == "faq":
        return {"faqs": site.get_faqs(page_id)}
    if suggestion.type in {"jsonld", "snippet"}:
        return {"jsonld": site.get_jsonld(page_id)}
    if suggestion.type == "link":
        return {"links": site.get_links(page_id)}
    return {}


def _serialize(
    suggestion: Suggestion,
    change_log: ChangeLogEntry,
    site: WordPressSite,
) -> SuggestionRecord:
    change_payload = {
        "id": change_log.id or 0,
        "status": change_log.status,
        "created_at": change_log.created_at,
        "executed_at": change_log.executed_at,
        "executed_by": change_log.executed_by,
        "decision_reason": change_log.decision_reason,
        "payload": change_log.payload_json,
        "diff_snapshot": change_log.diff_snapshot,
    }
    change_obj = ChangeLogInfo(**change_payload)
    return SuggestionRecord(
        id=suggestion.id or 0,
        type=suggestion.type,
        target=suggestion.target,
        status=suggestion.status,
        created_at=suggestion.created_at,
        reviewed_at=suggestion.reviewed_at,
        reviewed_by=suggestion.reviewed_by,
        decision_reason=suggestion.decision_reason,
        anomaly_id=suggestion.anomaly_id,
        payload=suggestion.payload_json,
        change_log=change_obj,
        current_state=_current_state(suggestion, site),
    )


@router.get("/suggestions", response_model=SuggestionListResponse)
def list_suggestions(
    status: str = "pending",
    type: str | None = None,
    claims: Dict[str, Any] = Depends(require_ops_claims),
    session: DatabaseSession = Depends(get_db),
    site: WordPressSite = Depends(get_wordpress),
) -> SuggestionListResponse:
    """Return suggestions awaiting review with the current page state."""

    _authorise(claims)
    suggestions = session.list_suggestions()
    items: List[SuggestionRecord] = []
    status_filter = status.lower() if status else None
    type_filter = type.lower() if type else None

    if status_filter and status_filter not in (_VALID_STATUS | {"all"}):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status filter")
    if type_filter and type_filter not in _VALID_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid suggestion type")

    for suggestion in suggestions:
        if status_filter and status_filter != "all" and suggestion.status != status_filter:
            continue
        if type_filter and suggestion.type != type_filter:
            continue
        if suggestion.type not in _VALID_TYPES and type_filter:
            continue
        change_log = session.get_change_log_for_suggestion(suggestion.id or 0)
        if change_log is None:
            # orphaned suggestion, skip for now
            continue
        items.append(_serialize(suggestion, change_log, site))

    return SuggestionListResponse(items=items)


def _apply_suggestion(suggestion: Suggestion, site: WordPressSite) -> Dict[str, Any]:
    payload = suggestion.payload_json
    if suggestion.type == "meta":
        before, after = site.apply_meta(suggestion.target, payload)
        return {"before": before, "after": after}
    if suggestion.type == "faq":
        before, after = site.append_faq(suggestion.target, payload)
        return {"before": before, "after": after}
    if suggestion.type in {"jsonld", "snippet"}:
        data = payload.get("data") if isinstance(payload, dict) else None
        body = data if isinstance(data, dict) else payload
        if not isinstance(body, dict):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON-LD payload")
        before, after = site.apply_jsonld(suggestion.target, body)
        return {"before": before, "after": after}
    if suggestion.type == "link":
        if not isinstance(payload, dict):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid link payload")
        before, after = site.add_internal_link(suggestion.target, payload)
        return {"before": before, "after": after}
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported suggestion type {suggestion.type}")


@router.post("/{suggestion_id}/approve", response_model=ReviewActionResponse, status_code=status.HTTP_200_OK)
def approve_suggestion(
    suggestion_id: int,
    claims: Dict[str, Any] = Depends(require_ops_claims),
    session: DatabaseSession = Depends(get_db),
    site: WordPressSite = Depends(get_wordpress),
) -> ReviewActionResponse:
    """Approve a suggestion and apply it through the WordPress client."""

    actor = _authorise(claims)
    suggestion = session.get_suggestion(suggestion_id)
    if suggestion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suggestion not found")
    if suggestion.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Suggestion already processed")

    change_log = session.get_change_log_for_suggestion(suggestion_id)
    if change_log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change log not found")

    diff = _apply_suggestion(suggestion, site)
    now = datetime.now(timezone.utc)
    suggestion.status = "approved"
    suggestion.reviewed_at = now
    suggestion.reviewed_by = actor
    suggestion.decision_reason = None

    change_log.status = "executed"
    change_log.executed_at = now
    change_log.executed_by = actor
    change_log.decision_reason = None
    change_log.diff_snapshot = diff

    record = _serialize(suggestion, change_log, site)
    return ReviewActionResponse(suggestion=record)


@router.post("/{suggestion_id}/reject", response_model=ReviewActionResponse, status_code=status.HTTP_200_OK)
def reject_suggestion(
    suggestion_id: int,
    request: ReviewDecisionRequest,
    claims: Dict[str, Any] = Depends(require_ops_claims),
    session: DatabaseSession = Depends(get_db),
    site: WordPressSite = Depends(get_wordpress),
) -> ReviewActionResponse:
    """Reject a suggestion and capture the decision reason."""

    actor = _authorise(claims)
    suggestion = session.get_suggestion(suggestion_id)
    if suggestion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suggestion not found")
    if suggestion.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Suggestion already processed")

    change_log = session.get_change_log_for_suggestion(suggestion_id)
    if change_log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change log not found")

    now = datetime.now(timezone.utc)
    suggestion.status = "rejected"
    suggestion.reviewed_at = now
    suggestion.reviewed_by = actor
    suggestion.decision_reason = request.decision_reason

    change_log.status = "rejected"
    change_log.decision_reason = request.decision_reason

    record = _serialize(suggestion, change_log, site)
    return ReviewActionResponse(suggestion=record)


__all__ = ["router", "list_suggestions", "approve_suggestion", "reject_suggestion"]

