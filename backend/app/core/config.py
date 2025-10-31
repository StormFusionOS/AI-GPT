import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from functools import lru_cache

from pydantic import AnyUrl, BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class WordPressSiteConfig(BaseModel):
    """Configuration payload for WordPress plugin security scanning."""

    name: str
    base_url: AnyUrl
    username: str
    application_password: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    project_name: str = 'AI SEO Dashboard'
    environment: str = 'development'

    backend_cors_origins: list[str] = ['http://localhost:5173']

    secret_key: str = 'change-me'
    access_token_expire_minutes: int = 30

    database_url: AnyUrl = 'postgresql+psycopg://postgres:postgres@localhost:5432/ai_seo_dashboard'
    redis_url: AnyUrl = 'redis://localhost:6379/0'

    qdrant_url: AnyUrl = 'http://localhost:6333'
    qdrant_api_key: str | None = None

    media_root: str = 'media'
    backup_root: str = '/mnt/backup'
    backup_retention_count: int = 7
    app_log_path: str = 'logs/app.log'
    task_log_path: str = 'logs/tasks.log'
    scheduler_state_path: str = 'storage/schedules.json'
    alerts_state_path: str = 'storage/alerts.json'
    integrity_state_path: str = 'storage/integrity_checksums.json'
    integrity_watch_paths: list[str] = ['.env', 'backend/app/core/config.py']
    log_alert_keywords: list[str] = ['ERROR', 'CRITICAL', 'Exception']
    wordpress_sites: list[WordPressSiteConfig] = []


    @field_validator('integrity_watch_paths', mode='before')
    @classmethod
    def _parse_integrity_watch_paths(cls, value: object) -> list[str] | object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(',') if item.strip()]
        return value

    @field_validator('wordpress_sites', mode='before')
    @classmethod
    def _parse_wordpress_sites(cls, value: object) -> list[WordPressSiteConfig] | object:
        if isinstance(value, str):
            try:
                data = json.loads(value)
            except json.JSONDecodeError as exc:  # pragma: no cover - configuration error path
                raise ValueError('WORDPRESS_SITES must be JSON encoded') from exc
            return data
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]


settings = get_settings()
