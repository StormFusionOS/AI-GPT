"""Utility helpers for AI powered workflows (validation, logging wrappers, etc.)."""
from __future__ import annotations

import json
from typing import Callable, Optional

import structlog
from pydantic import BaseModel, ValidationError

logger = structlog.get_logger(__name__)


class LLMJSONValidator:
    """Validate LLM JSON outputs and retry when the payload is malformed."""

    def __init__(
        self,
        schema_model: type[BaseModel],
        max_retries: int = 2,
        repair_prompt: Optional[Callable[[str], str]] = None,
    ) -> None:
        self.schema_model = schema_model
        self.max_retries = max_retries
        self.repair_prompt = repair_prompt

    def parse(self, raw: str) -> BaseModel:
        """Validate the JSON payload against the schema and retry on failures."""

        attempt = 0
        last_error: Optional[Exception] = None
        payload = raw
        while attempt <= self.max_retries:
            attempt += 1
            try:
                data = json.loads(payload)
                return self.schema_model.model_validate(data)
            except (json.JSONDecodeError, ValidationError) as exc:
                last_error = exc
                logger.warning("llmjsonvalidator.retry", attempt=attempt, error=str(exc))
                if attempt > self.max_retries:
                    break
                if self.repair_prompt:
                    payload = self.repair_prompt(payload)
                else:
                    # Last resort: wrap payload inside JSON string so humans can inspect.
                    payload = json.dumps({"raw": payload})
        raise ValidationError.from_exception_data(
            self.schema_model.__name__,
            [
                {
                    "type": "json_parsing_error",
                    "loc": ("payload",),
                    "msg": f"Failed to parse LLM output after {self.max_retries} retries",
                    "input": payload,
                }
            ],
        ) from last_error

