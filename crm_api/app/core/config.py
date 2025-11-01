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
    database_url: str = os.getenv("CRM_DATABASE_URL", "sqlite:///./crm.db")
    allowed_origins: List[str] | None = None
    facebook_verify_token: str = os.getenv("CRM_FACEBOOK_VERIFY_TOKEN", "fb-test-token")
    google_leads_verify_key: str = os.getenv("CRM_GOOGLE_LEADS_KEY", "google-test-key")
    twilio_auth_token: str = os.getenv("CRM_TWILIO_AUTH_TOKEN", "twilio-test-token")
    email_poll_enabled: bool = os.getenv("CRM_EMAIL_POLL_ENABLED", "false").lower() == "true"
    email_poll_interval_seconds: int = int(os.getenv("CRM_EMAIL_POLL_INTERVAL", "300"))
    email_poll_sample_path: str | None = os.getenv("CRM_EMAIL_POLL_SAMPLE_PATH")

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
