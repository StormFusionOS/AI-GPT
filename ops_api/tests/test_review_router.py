from __future__ import annotations

import json
from typing import Dict

import pytest

from app.db import DatabaseSession
from app.schemas.ai import MetaSuggestion
from app.schemas.review import ReviewDecisionRequest
from ops_api.ai.pipeline import GenerationPipeline, GenerationRequest
from app.api.routes import review


def _claims(role: str = "SEO_ENGINEER") -> Dict[str, str]:
    return {"sub": "ops@example.com", "role": role}


def _meta_payload(title: str, description: str) -> str:
    return json.dumps(
        {
            "title": title,
            "description": description,
            "primary_keyword": "hvac",
            "secondary_keywords": ["cooling", "service"],
        }
    )


def test_list_suggestions_includes_current_state(
    db_session: DatabaseSession, wordpress_site
) -> None:
    wordpress_site.seed_page("/services/hvac", meta={"title": "Current", "description": "Existing"})
    pipeline = GenerationPipeline(session=db_session, llm=lambda prompt: _meta_payload("New", "Updated"))
    request = GenerationRequest(
        template_id="meta_update",
        suggestion_type="meta",
        target="/services/hvac",
        model=MetaSuggestion,
        payload={"page_id": "/services/hvac"},
    )
    pipeline.generate(request)

    response = review.list_suggestions(
        claims=_claims(),
        session=db_session,
        site=wordpress_site,
    )

    assert len(response.items) == 1
    record = response.items[0]
    assert record.type == "meta"
    assert record.current_state["meta"]["title"] == "Current"
    assert record.payload["title"] == "New"


def test_approve_suggestion_updates_wordpress(
    db_session: DatabaseSession, wordpress_site
) -> None:
    wordpress_site.seed_page("/services/hvac", meta={"title": "Old", "description": "Prior"})
    pipeline = GenerationPipeline(session=db_session, llm=lambda prompt: _meta_payload("New Title", "Fresh desc"))
    request = GenerationRequest(
        template_id="meta_update",
        suggestion_type="meta",
        target="/services/hvac",
        model=MetaSuggestion,
        payload={"page_id": "/services/hvac"},
    )
    result = pipeline.generate(request)
    suggestion_id = result.suggestion.id or 0

    response = review.approve_suggestion(
        suggestion_id=suggestion_id,
        claims=_claims(),
        session=db_session,
        site=wordpress_site,
    )

    updated = response.suggestion
    assert updated.status == "approved"
    assert updated.change_log.status == "executed"
    assert updated.change_log.executed_at is not None
    assert updated.change_log.diff_snapshot["before"]["title"] == "Old"
    assert updated.change_log.diff_snapshot["after"]["title"] == "New Title"
    current_meta = wordpress_site.get_meta("/services/hvac")
    assert current_meta["title"] == "New Title"


def test_reject_suggestion_records_reason(
    db_session: DatabaseSession, wordpress_site
) -> None:
    wordpress_site.seed_page("/services/hvac", meta={"title": "Keep", "description": "Leave as is"})
    pipeline = GenerationPipeline(session=db_session, llm=lambda prompt: _meta_payload("Alt", "Different"))
    request = GenerationRequest(
        template_id="meta_update",
        suggestion_type="meta",
        target="/services/hvac",
        model=MetaSuggestion,
        payload={"page_id": "/services/hvac"},
    )
    result = pipeline.generate(request)
    suggestion_id = result.suggestion.id or 0

    response = review.reject_suggestion(
        suggestion_id=suggestion_id,
        request=ReviewDecisionRequest(decision_reason="Not aligned with branding"),
        claims=_claims(),
        session=db_session,
        site=wordpress_site,
    )

    record = response.suggestion
    assert record.status == "rejected"
    assert record.decision_reason == "Not aligned with branding"
    assert record.change_log.status == "rejected"
    assert wordpress_site.get_meta("/services/hvac")["title"] == "Keep"


def test_requires_authorised_role(db_session: DatabaseSession, wordpress_site) -> None:
    pipeline = GenerationPipeline(session=db_session, llm=lambda prompt: _meta_payload("New", "Updated"))
    request = GenerationRequest(
        template_id="meta_update",
        suggestion_type="meta",
        target="/services/hvac",
        model=MetaSuggestion,
        payload={"page_id": "/services/hvac"},
    )
    result = pipeline.generate(request)
    suggestion_id = result.suggestion.id or 0

    with pytest.raises(Exception):
        review.approve_suggestion(
            suggestion_id=suggestion_id,
            claims=_claims(role="SALES"),
            session=db_session,
            site=wordpress_site,
        )
