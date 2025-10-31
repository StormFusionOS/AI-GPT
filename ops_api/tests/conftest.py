"""Pytest fixtures for ops API."""
from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
OPS_ROOT = Path(__file__).resolve().parents[1]
if str(OPS_ROOT) not in sys.path:
    sys.path.insert(0, str(OPS_ROOT))

from app.core import config as config_module
from app.core.config import Settings, get_settings
from app.db import DatabaseSession, get_database, reset_database
from ops_api.orchestrator import celery_app as orchestrator_app
from ops_api.orchestrator.idempotency import get_idempotency_store


@pytest.fixture(scope="session", autouse=True)
def override_settings() -> Generator[None, None, None]:
    def _settings() -> Settings:
        return Settings(
            database_url="sqlite:///unused",
            allowed_origins=["http://testserver"],
            secret_key="ops-secret",
            celery_broker_url="memory://",
            celery_result_backend="rpc://",
            redis_url="memory://",
            celery_task_always_eager=True,
        )

    config_module.get_settings.cache_clear()  # type: ignore[attr-defined]
    config_module.get_settings = _settings  # type: ignore[assignment]
    previous_eager = orchestrator_app.conf.task_always_eager
    previous_propagate = orchestrator_app.conf.task_eager_propagates
    orchestrator_app.conf.task_always_eager = True
    orchestrator_app.conf.task_eager_propagates = False
    yield
    orchestrator_app.conf.task_always_eager = previous_eager
    orchestrator_app.conf.task_eager_propagates = previous_propagate
    config_module.get_settings = get_settings  # type: ignore[assignment]


@pytest.fixture(autouse=True)
def clean_state() -> Generator[None, None, None]:
    reset_database()
    get_idempotency_store().reset()
    yield


@pytest.fixture()
def db_session() -> Generator[DatabaseSession, None, None]:
    session = DatabaseSession(get_database())
    try:
        yield session
    finally:
        session.close()
