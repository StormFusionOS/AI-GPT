"""Tests for anomaly automation orchestration."""
from __future__ import annotations

from typing import Dict

import pytest

from app.db import DatabaseSession
from app.models import Anomaly
from ops_api.automation.anomaly_router import process_anomaly
from app.schemas.anomaly import ProcessAnomalyRequest


def _claims(role: str = "SEO_ENGINEER") -> Dict[str, str]:
    return {"sub": "ops@example.com", "role": role}


def test_process_anomaly_generates_multiple_suggestions(db_session: DatabaseSession) -> None:
    anomaly = db_session.add(
        Anomaly(
            page_id="/services/hvac",
            type="metadata_gap",
            summary="Meta title is underperforming and FAQ coverage missing",
            proposed_actions=["update_meta", "add_faq"],
        )
    )

    response = process_anomaly(
        anomaly_id=anomaly.id or 0,
        request=ProcessAnomalyRequest(),
        claims=_claims(),
        session=db_session,
    )

    assert response.created == 2
    assert len(response.suggestion_ids) == 2
    assert response.anomaly_id == anomaly.id
    assert response.skipped_actions == []

    suggestions = db_session.list_suggestions()
    assert len(suggestions) == 2
    assert {suggestion.anomaly_id for suggestion in suggestions} == {anomaly.id}

    changes = db_session.list_change_log()
    assert len(changes) == 2
    assert {change.anomaly_id for change in changes} == {anomaly.id}


def test_process_anomaly_unknown_action_skipped(db_session: DatabaseSession) -> None:
    anomaly = db_session.add(
        Anomaly(
            page_id="/services/plumbing",
            type="snippet_gap",
            summary="Featured snippet opportunity detected",
            proposed_actions=["add_snippet", "unsupported_action"],
        )
    )

    response = process_anomaly(
        anomaly_id=anomaly.id or 0,
        request=ProcessAnomalyRequest(),
        claims=_claims(),
        session=db_session,
    )

    assert response.created == 1
    assert response.skipped_actions == ["unsupported_action"]


def test_process_anomaly_requires_authorised_role(db_session: DatabaseSession) -> None:
    anomaly = db_session.add(
        Anomaly(
            page_id="/services/roofing",
            type="meta_gap",
            summary="Needs better snippet",
            proposed_actions=["add_snippet"],
        )
    )

    with pytest.raises(Exception):
        process_anomaly(
            anomaly_id=anomaly.id or 0,
            request=ProcessAnomalyRequest(),
            claims=_claims(role="SALES"),
            session=db_session,
        )
