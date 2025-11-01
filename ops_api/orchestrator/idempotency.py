"""Idempotency helpers for orchestrated tasks."""
from __future__ import annotations

import hashlib
import json
import threading
from typing import Any, Tuple

try:  # pragma: no cover - optional redis import for production usage
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore

from app.core.config import get_settings


class IdempotencyStore:
    """Redis-backed idempotency helper with in-memory fallback."""

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
        self._reserved: set[str] = set()
        self._inflight: set[str] = set()
        self._completed: set[str] = set()
        self._lock = threading.Lock()

    def _hash(self, task_name: str, payload: dict[str, Any]) -> str:
        payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(f"{task_name}:{payload_json}".encode("utf-8")).hexdigest()

    def _redis_key(self, key: str, suffix: str) -> str:
        return f"ops-idem:{suffix}:{key}"

    def _reserve_redis(self, key: str) -> bool:
        assert self._client is not None
        return bool(self._client.set(name=self._redis_key(key, "reserved"), value="1", nx=True, ex=self._ttl))

    def _inflight_redis(self, key: str, value: str) -> None:
        assert self._client is not None
        if value == "start":
            self._client.set(name=self._redis_key(key, "inflight"), value="1", ex=self._ttl)
        elif value == "finish":
            self._client.delete(self._redis_key(key, "inflight"))

    def _completed_redis(self, key: str, value: bool) -> None:
        assert self._client is not None
        if value:
            self._client.set(name=self._redis_key(key, "done"), value="1", ex=self._ttl)
        else:
            self._client.delete(self._redis_key(key, "done"))

    def reserve(self, task_name: str, payload: dict[str, Any], *, override_key: str | None = None) -> Tuple[bool, str]:
        key = override_key or self._hash(task_name, payload)
        if self._client is not None:
            added = self._reserve_redis(key)
            return added, key
        with self._lock:
            if key in self._reserved or key in self._inflight or key in self._completed:
                return False, key
            self._reserved.add(key)
            return True, key

    def try_start(self, task_name: str, payload: dict[str, Any], *, override_key: str | None = None) -> Tuple[bool, str]:
        key = override_key or self._hash(task_name, payload)
        if self._client is not None:
            # Redis fallback: use reserve semantics and inflight marker
            if not self._client.set(name=self._redis_key(key, "inflight"), value="1", nx=True, ex=self._ttl):
                return False, key
            if not self._client.exists(self._redis_key(key, "reserved")):
                self._client.set(name=self._redis_key(key, "reserved"), value="1", ex=self._ttl)
            return True, key
        with self._lock:
            if key in self._completed or key in self._inflight:
                return False, key
            if key not in self._reserved:
                self._reserved.add(key)
            self._inflight.add(key)
            return True, key

    def finish(self, key: str, *, outcome: str) -> None:
        if self._client is not None:
            if outcome == "SUCCESS" or outcome == "IGNORED":
                self._completed_redis(key, True)
                self._client.delete(self._redis_key(key, "reserved"))
            elif outcome == "FAILURE":
                self._completed_redis(key, False)
                self._client.delete(self._redis_key(key, "reserved"))
            elif outcome == "RETRY":
                self._completed_redis(key, False)
            self._inflight_redis(key, "finish")
            return
        with self._lock:
            self._inflight.discard(key)
            if outcome in {"SUCCESS", "IGNORED"}:
                self._completed.add(key)
                self._reserved.discard(key)
            elif outcome == "FAILURE":
                self._reserved.discard(key)
            elif outcome == "RETRY":
                # keep reserved so the retry attempt can proceed
                pass

    def reset(self) -> None:
        if self._client is not None:
            # best effort clean-up
            for suffix in ("reserved", "inflight", "done"):
                pattern = self._redis_key("*", suffix)
                for key in self._client.scan_iter(match=pattern):  # pragma: no cover - optional
                    self._client.delete(key)
        with self._lock:
            self._reserved.clear()
            self._inflight.clear()
            self._completed.clear()


_idempotency_store: IdempotencyStore | None = None


def get_idempotency_store() -> IdempotencyStore:
    global _idempotency_store
    if _idempotency_store is None:
        _idempotency_store = IdempotencyStore()
    return _idempotency_store
