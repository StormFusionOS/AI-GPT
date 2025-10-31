"""Service health snapshot model."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Integer, String

from ..db import Base, OPS_SCHEMA


class ServiceHealth(Base):
    """Captures the latest health probe for an infrastructure component."""

    __tablename__ = "service_health"
    __table_args__ = ({"schema": OPS_SCHEMA},)

    id = Column(Integer, primary_key=True, index=True)
    service = Column(String(100), nullable=False, unique=True)
    status = Column(String(10), nullable=False, default="ok")
    latency_ms = Column(Integer, nullable=True)
    details = Column(JSON, nullable=True)
    checked_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    def update(self, *, status: str, latency_ms: int | None = None, details: dict | None = None) -> None:
        self.status = status
        self.latency_ms = latency_ms
        self.details = details or {}
        self.checked_at = datetime.now(timezone.utc)
