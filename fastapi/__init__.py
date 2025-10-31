"""Lightweight FastAPI stub for offline testing.

This module provides a tiny subset of FastAPI's interface sufficient for unit
tests that call endpoint handlers directly. It is **not** a drop-in
replacement for the real framework but enables static imports without pulling
network dependencies in the execution environment.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


class HTTPException(Exception):
    """Exception carrying HTTP-style metadata."""

    def __init__(self, status_code: int, detail: str | Dict[str, Any] | None = None):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class _Status:
    HTTP_200_OK = 200
    HTTP_202_ACCEPTED = 202
    HTTP_204_NO_CONTENT = 204
    HTTP_400_BAD_REQUEST = 400
    HTTP_401_UNAUTHORIZED = 401
    HTTP_403_FORBIDDEN = 403
    HTTP_404_NOT_FOUND = 404
    HTTP_500_INTERNAL_SERVER_ERROR = 500


status = _Status()


@dataclass
class _Route:
    method: str
    path: str
    handler: Callable[..., Any]


class APIRouter:
    """Minimal router storing handlers for inclusion on the app."""

    def __init__(self, prefix: str = "", tags: Optional[List[str]] = None):
        self.prefix = prefix
        self.tags = tags or []
        self.routes: List[_Route] = []

    def get(self, path: str, **_: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._add_route("GET", path)

    def post(self, path: str, **_: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._add_route("POST", path)

    def delete(self, path: str, **_: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._add_route("DELETE", path)

    def _add_route(self, method: str, path: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.routes.append(_Route(method=method, path=f"{self.prefix}{path}", handler=func))
            return func

        return decorator


class FastAPI:
    """Simplified FastAPI application container."""

    def __init__(self, title: str | None = None):
        self.title = title or "Application"
        self.routes: List[_Route] = []

    def add_middleware(self, *_: Any, **__: Any) -> None:  # pragma: no cover - no-op
        return None

    def include_router(self, router: APIRouter, prefix: str = "") -> None:
        for route in router.routes:
            self.routes.append(_Route(route.method, f"{prefix}{route.path}", route.handler))

    def get(self, path: str, **_: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        router = APIRouter()
        decorator = router.get(path)
        self.include_router(router)
        return decorator
def Depends(dependency: Callable[..., Any]):  # type: ignore[override]
    """Return the dependency callable for manual invocation in tests."""

    return dependency


class Query:
    """Placeholder for query parameter metadata."""

    def __init__(self, default: Any = None, **_: Any):
        self.default = default


class Header(Query):
    """Header metadata wrapper (shares Query behavior)."""


__all__ = [
    "APIRouter",
    "FastAPI",
    "HTTPException",
    "status",
    "Depends",
    "Query",
    "Header",
]

