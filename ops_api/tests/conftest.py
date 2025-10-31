"""Pytest fixtures for ops API."""
from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest

from app.core import config as config_module
from app.core.config import Settings, get_settings
from app.db import Base, SessionLocal, engine, init_db, reset_engine
from ops_api.orchestrator import celery_app as orchestrator_app


TEST_DB = Path("ops-test.db")


@pytest.fixture(scope="session", autouse=True)
def override_settings() -> Generator[None, None, None]:
    def _settings() -> Settings:
        return Settings(
            database_url="sqlite:///./ops-test.db",
            allowed_origins=["http://testserver"],
            secret_key="ops-secret",
            celery_broker_url="memory://",
            celery_result_backend="rpc://",
            redis_url="memory://",
            celery_task_always_eager=True,
        )

    config_module.get_settings.cache_clear()  # type: ignore[attr-defined]
    config_module.get_settings = _settings  # type: ignore[assignment]
    reset_engine()
    init_db()
    previous_eager = orchestrator_app.conf.task_always_eager
    previous_propagate = orchestrator_app.conf.task_eager_propagates
    orchestrator_app.conf.task_always_eager = True
    orchestrator_app.conf.task_eager_propagates = False
    yield
    orchestrator_app.conf.task_always_eager = previous_eager
    orchestrator_app.conf.task_eager_propagates = previous_propagate
    config_module.get_settings = get_settings  # type: ignore[assignment]
    if TEST_DB.exists():
        TEST_DB.unlink()


@pytest.fixture(autouse=True)
def clean_db() -> Generator[None, None, None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    SessionLocal.close_all()


@pytest.fixture()
def db_session(override_settings: None) -> Generator:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
