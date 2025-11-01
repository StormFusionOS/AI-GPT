"""Schemas for anomaly automation endpoints."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ProcessAnomalyRequest(BaseModel):
    """Optional overrides when processing an anomaly."""

    actions: Optional[List[str]] = Field(
        default=None,
        description="Optional subset of actions to execute instead of the stored proposed actions.",
    )


class ProcessAnomalyResponse(BaseModel):
    """Response payload after generating suggestions for an anomaly."""

    anomaly_id: int
    created: int
    suggestion_ids: List[int]
    skipped_actions: List[str] = Field(default_factory=list)
