"""Pytest fixtures for ops API."""
from __future__ import annotations

import os, sys

USE_STUBS = os.getenv("USE_TEST_STUBS", "0") == "1"
if USE_STUBS:
    import test_stubs.fastapi_stub as fastapi_stub
    import test_stubs.pydantic_stub as pydantic_stub
    import test_stubs.structlog_stub as structlog_stub
    import test_stubs.celery_stub as celery_stub

    sys.modules.setdefault("fastapi", fastapi_stub)
    sys.modules.setdefault("fastapi.middleware.cors", fastapi_stub)
    sys.modules.setdefault("pydantic", pydantic_stub)
    sys.modules.setdefault("structlog", structlog_stub)
    sys.modules.setdefault("celery", celery_stub)
    sys.modules.setdefault("celery.exceptions", celery_stub)
    sys.modules.setdefault("celery.utils.log", celery_stub)

from collections.abc import Generator
from pathlib import Path

import importlib
import pytest

from ops_api.app.services.wordpress import get_wordpress_site, reset_wordpress_site

OPS_ROOT = Path(__file__).resolve().parents[1]
if str(OPS_ROOT) not in sys.path:
    sys.path.insert(0, str(OPS_ROOT))
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
CRM_ROOT = ROOT / "crm_api"
if str(CRM_ROOT) in sys.path:
    sys.path.remove(str(CRM_ROOT))

for module_name in [
    "app",
    "app.core",
    "app.core.config",
    "app.db",
    "app.api",
    "app.api.routes",
    "app.models",
    "test_auth",
    "test_contacts",
    "test_status",
    "fastapi",
    "fastapi.middleware",
]:
    sys.modules.pop(module_name, None)
ops_package = importlib.import_module("ops_api.app")
sys.modules["app"] = ops_package
for submodule in [
    "core",
    "core.config",
    "db",
    "api",
    "models",
    "schemas",
    "schemas.review",
    "api.routes",
]:
    module = importlib.import_module(f"ops_api.app.{submodule}")
    sys.modules[f"app.{submodule}"] = module

fastapi_pkg = importlib.import_module("ops_api.fastapi")
sys.modules["fastapi"] = fastapi_pkg
for submodule in [
    "middleware",
    "middleware.cors",
]:
    module = importlib.import_module(f"ops_api.fastapi.{submodule}")
    sys.modules[f"fastapi.{submodule}"] = module

from app.core import config as config_module
from app.core.config import Settings, get_settings
from app.db import DatabaseSession, get_database, reset_database


@pytest.fixture(scope="session", autouse=True)
def override_settings() -> Generator[None, None, None]:
    artifacts = ROOT / "tmp-test-artifacts"
    artifacts.mkdir(exist_ok=True)
    backup_root = artifacts / "backups"
    nas_path = artifacts / "nas"
    backup_root.mkdir(exist_ok=True)
    nas_path.mkdir(exist_ok=True)

    def _settings() -> Settings:
        return Settings(
            database_url="sqlite:///unused",
            allowed_origins=["http://testserver"],
            secret_key="ops-secret",
            celery_broker_url="memory://",
            celery_result_backend="rpc://",
            redis_url="memory://",
            celery_task_always_eager=True,
            backup_root=backup_root,
            backup_nas_path=str(nas_path),
            ops_pg_dsn="postgresql://ops:pass@localhost/ops",
            crm_pg_dsn="postgresql://crm:pass@localhost/crm",
            ops_pg_admin_dsn="postgresql://postgres:pass@localhost/postgres",
        )

    config_module.get_settings.cache_clear()  # type: ignore[attr-defined]
    config_module.get_settings = _settings  # type: ignore[assignment]

    from ops_api.orchestrator import celery_app as orchestrator_app

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
    from ops_api.orchestrator.idempotency import get_idempotency_store
    from ops_api.orchestrator.celery_app import celery_app
    from ops_api.orchestrator.scheduler import refresh_beat_schedule

    get_idempotency_store().reset()
    refresh_beat_schedule(celery_app)
    reset_wordpress_site()
    yield


@pytest.fixture()
def db_session() -> Generator[DatabaseSession, None, None]:
    session = DatabaseSession(get_database())
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def wordpress_site():
    site = get_wordpress_site()
    return site


