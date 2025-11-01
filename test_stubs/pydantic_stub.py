"""Minimal subset of Pydantic behaviour for tests."""
from __future__ import annotations

from typing import Any, Callable, Dict, TypeVar

T = TypeVar("T")


class BaseModel:
    """Simple attribute container emulating Pydantic's BaseModel."""

    def __init__(self, **data: Any) -> None:
        for key, value in data.items():
            setattr(self, key, value)

    def dict(self, *, exclude_none: bool = False) -> Dict[str, Any]:
        items = dict(self.__dict__)
        if exclude_none:
            items = {key: value for key, value in items.items() if value is not None}
        return items


def Field(default: Any = None, **_: Any) -> Any:
    return default


HttpUrl = str


def constr(**_: Any) -> type[str]:
    return str


def validator(*_: Any, **__: Any) -> Callable[[Callable[..., T]], Callable[..., T]]:
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        return func

    return decorator


__all__ = ["BaseModel", "Field", "HttpUrl", "constr", "validator"]
