"""Minimal structlog stub for offline tests."""
from __future__ import annotations

from typing import Any


class _Logger:
    def bind(self, **_: Any) -> "_Logger":  # pragma: no cover - passthrough
        return self

    def info(self, *_: Any, **__: Any) -> None:  # pragma: no cover - noop
        return None

    def warning(self, *_: Any, **__: Any) -> None:  # pragma: no cover
        return None

    def error(self, *_: Any, **__: Any) -> None:  # pragma: no cover
        return None


def get_logger(*_: Any, **__: Any) -> _Logger:  # pragma: no cover
    return _Logger()


__all__ = ["get_logger"]
