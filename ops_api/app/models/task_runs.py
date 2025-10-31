"""Task run persistence model."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text

from ..db import Base, OPS_SCHEMA


class TaskRun(Base):
    """Represents a single orchestrated task execution."""

    __tablename__ = "task_runs"
    __table_args__ = ({"schema": OPS_SCHEMA},)

    id = Column(Integer, primary_key=True, index=True)
    module = Column(String(50), nullable=False)
    task = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="queued")
    queued_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    retries = Column(Integer, nullable=False, default=0)
    message = Column(Text, nullable=True)
    payload_json = Column(JSON, nullable=True)

    def mark_running(self) -> None:
        self.status = "running"
        self.started_at = datetime.now(timezone.utc)

    def mark_finished(self, status: str, message: str | None = None) -> None:
        self.status = status
        self.finished_at = datetime.now(timezone.utc)
        if message is not None:
            self.message = message
