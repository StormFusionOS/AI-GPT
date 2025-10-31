"""Endpoints exposing AI tooling utilities."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import require_admin_role
from app.schemas import PromptDefinitionModel, PromptRunRequest, PromptRunResponse
from app.services import prompt_runner

router = APIRouter(prefix='/ai', tags=['ai'], dependencies=[Depends(require_admin_role)])


@router.get('/prompts', response_model=list[PromptDefinitionModel])
async def list_prompts() -> list[PromptDefinitionModel]:
    return [PromptDefinitionModel(**definition) for definition in prompt_runner.list_prompts()]


@router.post('/run_prompt', response_model=PromptRunResponse)
async def run_prompt(payload: PromptRunRequest) -> PromptRunResponse:
    result = await prompt_runner.run_prompt(prompt=payload.prompt, parameters=payload.parameters)
    return PromptRunResponse(**result)


__all__ = ['router']
