"""Unit tests for AI utility helpers to guarantee deterministic behaviour."""
from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from app.ai.utils import LLMJSONValidator


class SampleSchema(BaseModel):
    value: str


def test_llmjsonvalidator_parses_valid_payload() -> None:
    validator = LLMJSONValidator(SampleSchema)
    result = validator.parse('{"value": "ok"}')
    assert result.value == 'ok'


def test_llmjsonvalidator_retries_and_wraps_payload() -> None:
    validator = LLMJSONValidator(SampleSchema, max_retries=1, repair_prompt=lambda raw: '{"value": "fixed"}')
    result = validator.parse('not-json')
    assert result.value == 'fixed'


def test_llmjsonvalidator_raises_after_failures() -> None:
    validator = LLMJSONValidator(SampleSchema, max_retries=0)
    with pytest.raises(ValidationError):
        validator.parse('still not json')
