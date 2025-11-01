"""Stub CORSMiddleware."""
from __future__ import annotations

from typing import Any


class CORSMiddleware:  # pragma: no cover - acts as a no-op placeholder
    def __init__(self, app: Any, **_: Any) -> None:
        self.app = app
