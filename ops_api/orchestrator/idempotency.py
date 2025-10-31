"""Idempotency helpers for orchestrated tasks."""
from __future__ import annotations

import hashlib
import json
import threading
from typing import Any

try:  # pragma: no cover - optional redis import for production usage
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore

from app.core.config import get_settings


class IdempotencyStore:
    """Simple Redis-backed idempotency helper with in-memory fallback."""

    def __init__(self) -> None:
        settings = get_settings()
        self._ttl = settings.idempotency_ttl_seconds
        self._redis_url = settings.redis_url
        self._client = None
        if redis is not None and self._redis_url.startswith("redis://"):
            try:  # pragma: no cover - redis not available in tests
                self._client = redis.Redis.from_url(self._redis_url, decode_responses=True)
            except Exception:
                self._client = None
        self._memory_store: set[str] = set()
        self._lock = threading.Lock()

    def _hash(self, task_name: str, payload: dict[str, Any]) -> str:
        payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(f"{task_name}:{payload_json}".encode("utf-8")).hexdigest()
        return digest

    def register(self, task_name: str, payload: dict[str, Any], override_key: str | None = None) -> tuple[bool, str]:
        key = override_key or self._hash(task_name, payload)
        if self._client is not None:
            added = bool(self._client.set(name=f"ops-idem:{key}", value="1", nx=True, ex=self._ttl))
            return added, key
        with self._lock:
            if key in self._memory_store:
                return False, key
            self._memory_store.add(key)
            return True, key


_idempotency_store: IdempotencyStore | None = None


def get_idempotency_store() -> IdempotencyStore:
    global _idempotency_store
    if _idempotency_store is None:
        _idempotency_store = IdempotencyStore()
    return _idempotency_store
