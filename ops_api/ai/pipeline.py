"""AI generation pipeline with schema validation and retries."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Type, get_origin

from pydantic import BaseModel

from app.db import DatabaseSession
from app.models.change_log import ChangeLogEntry
from app.models.suggestion import Suggestion

LLMCallable = Callable[[str], str]


class GenerationError(RuntimeError):
    """Raised when the model fails to produce valid structured output."""


@dataclass
class GenerationRequest:
    """Request payload for a structured generation."""

    template_id: str
    suggestion_type: str
    target: str
    model: Type[BaseModel]
    payload: Dict[str, Any]


@dataclass
class GenerationResult:
    """Represents a successful generation event."""

    suggestion: Suggestion
    data: BaseModel


class GenerationPipeline:
    """Coordinates prompt rendering, validation, and persistence."""

    max_retries: int = 2

    def __init__(self, *, session: DatabaseSession, llm: LLMCallable) -> None:
        self._session = session
        self._llm = llm

    # ---- context + prompt helpers -------------------------------------------------
    def retrieve_context(
        self, *, page_id: Optional[str] = None, keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        """Return lightweight context used to prime the model."""

        if page_id:
            return {"page_id": page_id, "excerpt": f"Content summary for {page_id}."}
        if keyword:
            return {"keyword": keyword, "serp_snapshot": [f"Result for {keyword}"]}
        return {}

    def render_prompt(
        self, template_id: str, context: Dict[str, Any], payload: Dict[str, Any], model: Type[BaseModel]
    ) -> str:
        """Render a deterministic prompt with instructions for JSON output."""

        instruction = (
            "You are an SEO assistant. Produce JSON strictly matching the "
            f"{model.__name__} schema."
        )
        prompt = {
            "template": template_id,
            "instruction": instruction,
            "context": context,
            "payload": payload,
        }
        return json.dumps(prompt, ensure_ascii=False)

    # ---- generation ----------------------------------------------------------------
    def generate(self, request: GenerationRequest) -> GenerationResult:
        context = self.retrieve_context(
            page_id=request.payload.get("page_id"),
            keyword=request.payload.get("keyword"),
        )
        prompt = self.render_prompt(request.template_id, context, request.payload, request.model)
        errors: list[str] = []
        for attempt in range(self.max_retries + 1):
            raw = self._llm(prompt)
            try:
                data = self._parse_and_validate(raw, request.model)
            except ValueError as exc:
                errors.append(str(exc))
                if attempt >= self.max_retries:
                    raise GenerationError(
                        f"Unable to validate output after {attempt + 1} attempts: {'; '.join(errors)}"
                    ) from exc
                prompt = self.repair_on_fail(prompt, request.model, errors[-1])
                continue
            model_instance = request.model(**data)
            suggestion = Suggestion(
                type=request.suggestion_type,
                target=request.target,
                payload_json=model_instance.dict(),
            )
            suggestion = self._session.add(suggestion)  # assigns identifier
            change_log = ChangeLogEntry(
                type=request.suggestion_type,
                target=request.target,
                payload_json={
                    "suggestion_id": suggestion.id,
                    "template": request.template_id,
                    "diff": request.payload.get("diff"),
                },
            )
            self._session.add(change_log)
            return GenerationResult(suggestion=suggestion, data=model_instance)
        raise GenerationError("Max retries exceeded")

    # ---- validation helpers --------------------------------------------------------
    def _parse_and_validate(self, raw: str, model: Type[BaseModel]) -> Dict[str, Any]:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:  # pragma: no cover - kept for clarity
            raise ValueError("Response was not valid JSON") from exc
        if not isinstance(parsed, dict):
            raise ValueError("Expected JSON object")
        annotations = getattr(model, "__annotations__", {})
        missing = [name for name in annotations if name not in parsed]
        if missing:
            raise ValueError(f"Missing fields: {', '.join(missing)}")
        for field, annotation in annotations.items():
            value = parsed[field]
            origin = get_origin(annotation)
            if origin in {list, tuple} and not isinstance(value, list):
                raise ValueError(f"Field {field} must be a list")
            if origin in {dict} or annotation in {dict, Dict}:
                if not isinstance(value, dict):
                    raise ValueError(f"Field {field} must be an object")
        
        return parsed

    def repair_on_fail(self, prompt: str, model: Type[BaseModel], error: str) -> str:
        template = json.loads(prompt)
        template["instruction"] = (
            f"Previous output was invalid ({error}). Return only valid JSON matching schema {model.__name__}."
        )
        template["retry"] = template.get("retry", 0) + 1
        return json.dumps(template, ensure_ascii=False)


__all__ = [
    "GenerationPipeline",
    "GenerationRequest",
    "GenerationResult",
    "GenerationError",
]
