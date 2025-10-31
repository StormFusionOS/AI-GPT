"""Tests for the AI generation pipeline."""
from __future__ import annotations

import json
from collections.abc import Iterator

import pytest

from app.db import DatabaseSession
from app.schemas.ai import MetaSuggestion
from ops_api.ai.pipeline import GenerationPipeline, GenerationRequest, GenerationResult


class _LLMIterator:
    """Deterministic iterator for mocked LLM responses."""

    def __init__(self, responses: Iterator[str]) -> None:
        self._responses = iter(responses)
        self.prompts: list[str] = []

    def __call__(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return next(self._responses)


def test_pipeline_repairs_and_saves(db_session: DatabaseSession) -> None:
    llm = _LLMIterator(iter([
        "not json",
        json.dumps(
            {
                "title": "Optimised Title",
                "description": "Improved meta description.",
                "primary_keyword": "plumber",
                "secondary_keywords": ["emergency", "repairs"],
            }
        ),
    ]))
    pipeline = GenerationPipeline(session=db_session, llm=llm)
    request = GenerationRequest(
        template_id="meta",
        suggestion_type="meta",
        target="/services/plumbing",
        model=MetaSuggestion,
        payload={"page_id": "page-123"},
    )

    result = pipeline.generate(request)
    assert isinstance(result, GenerationResult)
    assert len(llm.prompts) == 2
    assert "Return only valid JSON" in llm.prompts[-1]

    suggestions = db_session.list_suggestions()
    assert len(suggestions) == 1
    suggestion = suggestions[0]
    assert suggestion.status == "pending"
    assert suggestion.payload_json["title"] == "Optimised Title"

    changes = db_session.list_change_log()
    assert len(changes) == 1
    change = changes[0]
    assert change.status == "pending"
    assert change.payload_json["suggestion_id"] == suggestion.id


def test_pipeline_exhausts_retries(db_session: DatabaseSession) -> None:
    llm = _LLMIterator(iter(["{}", "{}", "{}"]))
    pipeline = GenerationPipeline(session=db_session, llm=llm)
    request = GenerationRequest(
        template_id="meta",
        suggestion_type="meta",
        target="/services/plumbing",
        model=MetaSuggestion,
        payload={"keyword": "plumber"},
    )

    with pytest.raises(Exception):
        pipeline.generate(request)

    assert db_session.list_suggestions() == []
    assert db_session.list_change_log() == []
