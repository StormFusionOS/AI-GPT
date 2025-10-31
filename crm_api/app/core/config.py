"""CRM configuration utilities using environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import timedelta
from functools import lru_cache
from typing import List


@dataclass
class Settings:
    app_name: str = "CRM API"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = os.getenv("CRM_SECRET_KEY", "changeme")
    access_token_expire_minutes: int = int(os.getenv("CRM_ACCESS_TOKEN_MINUTES", "15"))
    refresh_token_expire_minutes: int = int(os.getenv("CRM_REFRESH_TOKEN_MINUTES", str(60 * 24)))
    database_url: str = os.getenv("CRM_DATABASE_URL", "memory://crm")
    allowed_origins: List[str] | None = None

    def __post_init__(self) -> None:
        if self.allowed_origins is None:
            self.allowed_origins = os.getenv("CRM_ALLOWED_ORIGINS", "https://crm.example.com").split(",")

    def access_token_ttl(self) -> timedelta:
        return timedelta(minutes=self.access_token_expire_minutes)

    def refresh_token_ttl(self) -> timedelta:
        return timedelta(minutes=self.refresh_token_expire_minutes)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
