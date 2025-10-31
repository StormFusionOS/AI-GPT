"""Pytest fixtures for CRM API."""
from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from uuid import uuid4

import pytest

import hashlib
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core import config as config_module
from app.core.config import Settings, get_settings
from app.db import DB, init_db
from app.models import User, UserRole


@pytest.fixture(scope="session", autouse=True)
def override_settings() -> Generator[None, None, None]:
    def _settings() -> Settings:
        return Settings(database_url="sqlite:///./test.db", allowed_origins=["http://testserver"], secret_key="test")

    config_module.get_settings.cache_clear()  # type: ignore[attr-defined]
    config_module.get_settings = _settings  # type: ignore[assignment]
    init_db()
    hashed = hashlib.sha256("password123".encode("utf-8")).hexdigest()
    DB.users["sales@example.com"] = User(id=uuid4(), email="sales@example.com", hashed_password=hashed, role=UserRole.SALES)
    yield
    config_module.get_settings = get_settings  # type: ignore[assignment]
