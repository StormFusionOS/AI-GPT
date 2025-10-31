"""Schemas for the review queue."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


StatusLiteral = Literal["pending", "approved", "rejected", "executed"]


class ChangeLogInfo(BaseModel):
    id: int
    status: StatusLiteral
    created_at: datetime
    executed_at: Optional[datetime] = None
    executed_by: Optional[str] = None
    decision_reason: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    diff_snapshot: Optional[Dict[str, Any]] = None


class SuggestionRecord(BaseModel):
    id: int
    type: str
    target: str
    status: StatusLiteral
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    decision_reason: Optional[str] = None
    anomaly_id: Optional[int] = None
    payload: Dict[str, Any]
    change_log: ChangeLogInfo
    current_state: Dict[str, Any]


class SuggestionListResponse(BaseModel):
    items: List[SuggestionRecord]


class ReviewDecisionRequest(BaseModel):
    decision_reason: str = Field(..., min_length=1, max_length=500)


class ReviewActionResponse(BaseModel):
    suggestion: SuggestionRecord

