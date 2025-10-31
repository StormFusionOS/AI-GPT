"""Ops API configuration utilities."""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import List


@dataclass
class Settings:
    app_name: str = "Ops API"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = os.getenv("OPS_SECRET_KEY", "changeme")
    access_token_expire_minutes: int = int(os.getenv("OPS_ACCESS_TOKEN_MINUTES", "10"))
    refresh_token_expire_minutes: int = int(os.getenv("OPS_REFRESH_TOKEN_MINUTES", "60"))
    database_url: str = os.getenv("OPS_DATABASE_URL", "sqlite:///./ops.db")
    redis_url: str = os.getenv("OPS_REDIS_URL", "redis://localhost:6379/0")
    celery_broker_url: str = os.getenv("OPS_CELERY_BROKER", os.getenv("OPS_REDIS_URL", "redis://localhost:6379/0"))
    celery_result_backend: str = os.getenv("OPS_CELERY_BACKEND", os.getenv("OPS_REDIS_URL", "redis://localhost:6379/0"))
    idempotency_ttl_seconds: int = int(os.getenv("OPS_IDEMPOTENCY_TTL", "3600"))
    celery_task_always_eager: bool = os.getenv("OPS_CELERY_EAGER", "false").lower() == "true"
    allowed_origins: List[str] | None = None

    def __post_init__(self) -> None:
        if self.allowed_origins is None:
            self.allowed_origins = os.getenv("OPS_ALLOWED_ORIGINS", "https://ops.example.com").split(",")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
