from functools import lru_cache

from pydantic import AnyUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


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


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]


settings = get_settings()
