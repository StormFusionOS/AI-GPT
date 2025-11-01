"""Schemas for alert responses."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AlertView(BaseModel):
    id: int
    level: str
    message: str
    created_at: datetime


class AlertListResponse(BaseModel):
    alerts: list[AlertView]
