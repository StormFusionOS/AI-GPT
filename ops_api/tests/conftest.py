"""Pytest fixtures for ops API."""
from __future__ import annotations

from collections.abc import Generator

import pytest

from app.core import config as config_module
from app.core.config import Settings, get_settings


@pytest.fixture(scope="session", autouse=True)
def override_settings() -> Generator[None, None, None]:
    def _settings() -> Settings:
        return Settings(database_url="sqlite:///./ops-test.db", allowed_origins=["http://testserver"], secret_key="ops-secret")

    config_module.get_settings.cache_clear()  # type: ignore[attr-defined]
    config_module.get_settings = _settings  # type: ignore[assignment]
    yield
    config_module.get_settings = get_settings  # type: ignore[assignment]
