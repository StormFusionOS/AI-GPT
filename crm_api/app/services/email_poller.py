"""Simple IMAP-like email poller that feeds the lead intake pipeline."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import structlog

from ..core.config import get_settings
from ..models import InteractionType
from .intake import ingest_lead

logger = structlog.get_logger(__name__)


@dataclass
class QueuedEmail:
    subject: str
    body: str
    source: str


class EmailPoller:
    """Pulls messages and converts them into CRM leads."""

    def __init__(self, interval_seconds: int, sample_path: Optional[str] = None) -> None:
        self.interval_seconds = interval_seconds
        self.sample_path = Path(sample_path) if sample_path else None
        self._queue: asyncio.Queue[QueuedEmail] = asyncio.Queue()
        self._task: asyncio.Task[None] | None = None

    def enqueue(self, subject: str, body: str, source: str) -> None:
        """Queue a message for ingestion (used by tests and optional sample loader)."""

        self._queue.put_nowait(QueuedEmail(subject=subject, body=body, source=source))

    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:  # pragma: no cover - cancellation path
                pass
            self._task = None

    async def poll_once(self) -> None:
        message = await self._dequeue()
        if not message:
            return
        payload = self._parse_email(message.subject, message.body)
        ingest_lead(
            name=payload.get("name", "Email Lead"),
            email=payload.get("email"),
            phone=payload.get("phone"),
            message=payload.get("message", message.body.strip()),
            source=message.source,
            inbound_type=InteractionType.EMAIL_IN,
        )
        logger.info("email-lead-ingested", source=message.source)

    async def _run(self) -> None:
        settings = get_settings()
        while True:
            await self.poll_once()
            await asyncio.sleep(self.interval_seconds or settings.email_poll_interval_seconds)

    async def _dequeue(self) -> QueuedEmail | None:
        if self.sample_path and self.sample_path.exists():
            # Load sample messages once per poll cycle.
            data = self.sample_path.read_text(encoding="utf-8")
            if data.strip():
                self.sample_path.write_text("", encoding="utf-8")
                self.enqueue("Sample Lead", data, "email_parser")
        try:
            return self._queue.get_nowait()
        except asyncio.QueueEmpty:
            return None

    @staticmethod
    def _parse_email(subject: str, body: str) -> dict[str, str]:
        """Parse key:value pairs from marketplace notification emails."""

        result: dict[str, str] = {"message": body.strip(), "subject": subject}
        for line in body.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()
            if key in {"name", "full name"}:
                result["name"] = value
            elif key in {"email", "email address"}:
                result["email"] = value
            elif key in {"phone", "phone number"}:
                result["phone"] = value
            elif key in {"details", "message", "description"}:
                result["message"] = value
        return result


__all__ = ["EmailPoller", "QueuedEmail"]
