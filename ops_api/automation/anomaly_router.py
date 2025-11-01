"""Automation endpoints for processing anomalies into AI suggestions."""
from __future__ import annotations

import json
from typing import Any, Dict, Mapping, MutableSequence, Sequence

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_claims, get_db
from app.db import DatabaseSession
from app.models import Anomaly
from app.schemas.ai import FAQItem, FeaturedSnippet, MetaSuggestion
from app.schemas.anomaly import ProcessAnomalyRequest, ProcessAnomalyResponse
from app.security import RoleGuard
from ops_api.ai.pipeline import GenerationPipeline, GenerationRequest

ALLOWED_ROLES = RoleGuard(["SEO_ENGINEER", "DEVOPS", "OWNER"])

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


class _ActionConfig(Dict[str, Any]):
    """Typed mapping for anomaly automation actions."""


ACTION_MAP: Mapping[str, _ActionConfig] = {
    "update_meta": {
        "template_id": "meta_update",
        "suggestion_type": "meta",
        "model": MetaSuggestion,
    },
    "add_faq": {
        "template_id": "faq",
        "suggestion_type": "faq",
        "model": FAQItem,
    },
    "add_snippet": {
        "template_id": "featured_snippet",
        "suggestion_type": "snippet",
        "model": FeaturedSnippet,
    },
}


def _default_llm(prompt: str) -> str:
    """Deterministic JSON payload for local development and tests."""

    payload = json.loads(prompt)
    template = payload.get("template")
    context = payload.get("context", {})
    req_payload = payload.get("payload", {})
    summary = req_payload.get("summary") or context.get("excerpt") or "Pending remediation"
    page_id = req_payload.get("page_id") or context.get("page_id") or "/"
    anomaly_type = req_payload.get("anomaly_type", "Anomaly")

    if template == "meta_update":
        data = {
            "title": f"Improved {anomaly_type.title()} for {page_id}",
            "description": f"{summary} — refreshed metadata to resolve the anomaly.",
            "primary_keyword": anomaly_type.lower(),
            "secondary_keywords": ["seo", "remediation"],
        }
    elif template == "faq":
        data = {
            "question": f"How does {anomaly_type.lower()} impact {page_id}?",
            "answer": f"{summary} This update clarifies the issue for visitors.",
        }
    elif template == "featured_snippet":
        keyword = req_payload.get("keyword") or anomaly_type.lower()
        data = {
            "query": keyword,
            "snippet": f"{summary} Optimised for quick answers.",
            "url": f"https://example.com{page_id}",
        }
    else:  # pragma: no cover - fallback for future templates
        data = {"data": {"note": summary}}
    return json.dumps(data, ensure_ascii=False)


def _authorise(claims: Dict[str, Any]) -> None:
    ALLOWED_ROLES(claims)


def _actions_from_request(anomaly: Anomaly, request: ProcessAnomalyRequest) -> Sequence[str]:
    if request.actions is not None:
        return request.actions
    return anomaly.proposed_actions


@router.post("/{anomaly_id}/process", response_model=ProcessAnomalyResponse, status_code=status.HTTP_202_ACCEPTED)
def process_anomaly(
    anomaly_id: int,
    request: ProcessAnomalyRequest | None = None,
    claims: Dict[str, Any] = Depends(get_claims),
    session: DatabaseSession = Depends(get_db),
) -> ProcessAnomalyResponse:
    """Generate AI suggestions for a stored anomaly without publishing them."""

    _authorise(claims)
    anomaly = session.get(Anomaly, anomaly_id)
    if anomaly is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anomaly not found")

    request = request or ProcessAnomalyRequest()
    actions = list(_actions_from_request(anomaly, request))
    if not actions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No actions provided")

    pipeline = GenerationPipeline(session=session, llm=_default_llm)
    created_ids: MutableSequence[int] = []
    skipped: MutableSequence[str] = []

    for action in actions:
        config = ACTION_MAP.get(action)
        if config is None:
            skipped.append(action)
            continue
        payload = {
            "page_id": anomaly.page_id,
            "summary": anomaly.summary,
            "anomaly_type": anomaly.type,
            "action": action,
        }
        request_model = GenerationRequest(
            template_id=config["template_id"],
            suggestion_type=config["suggestion_type"],
            target=anomaly.page_id,
            model=config["model"],
            payload=payload,
            anomaly_id=anomaly.id,
        )
        result = pipeline.generate(request_model)
        created_ids.append(result.suggestion.id or 0)

    if not created_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No actionable steps produced suggestions")

    return ProcessAnomalyResponse(
        anomaly_id=anomaly.id or anomaly_id,
        created=len(created_ids),
        suggestion_ids=list(created_ids),
        skipped_actions=list(skipped),
    )


__all__ = ["router", "process_anomaly"]
