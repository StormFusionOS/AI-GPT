"""Minimal FastAPI shim used exclusively in test environments."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


class HTTPException(Exception):
    """Exception carrying HTTP-like metadata."""

    def __init__(self, status_code: int, detail: str | Dict[str, Any] | None = None):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class _Status:
    HTTP_200_OK = 200
    HTTP_201_CREATED = 201
    HTTP_202_ACCEPTED = 202
    HTTP_204_NO_CONTENT = 204
    HTTP_400_BAD_REQUEST = 400
    HTTP_401_UNAUTHORIZED = 401
    HTTP_403_FORBIDDEN = 403
    HTTP_404_NOT_FOUND = 404
    HTTP_409_CONFLICT = 409
    HTTP_500_INTERNAL_SERVER_ERROR = 500


status = _Status()


@dataclass
class _Route:
    method: str
    path: str
    handler: Callable[..., Any]


class APIRouter:
    """Minimal router collecting registered routes."""

    def __init__(self, prefix: str = "", tags: Optional[List[str]] = None):
        self.prefix = prefix
        self.tags = tags or []
        self.routes: List[_Route] = []

    def _add_route(self, method: str, path: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.routes.append(_Route(method=method, path=f"{self.prefix}{path}", handler=func))
            return func

        return decorator

    def get(self, path: str, **_: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._add_route("GET", path)

    def post(self, path: str, **_: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._add_route("POST", path)

    def delete(self, path: str, **_: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._add_route("DELETE", path)


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


def Depends(dependency: Callable[..., Any]) -> Callable[..., Any]:  # type: ignore[override]
    """Return the dependency callable for direct invocation in tests."""

    return dependency


class Query:
    """Placeholder for query parameter metadata."""

    def __init__(self, default: Any = None, **_: Any):
        self.default = default


class Header(Query):
    """Header metadata wrapper (shares Query behaviour)."""


class CORSMiddleware:  # pragma: no cover - placeholder
    """No-op middleware placeholder for tests."""

    def __init__(self, app: Any, **_: Any) -> None:
        self.app = app


__all__ = [
    "APIRouter",
    "FastAPI",
    "HTTPException",
    "Header",
    "Query",
    "Depends",
    "status",
    "CORSMiddleware",
]
