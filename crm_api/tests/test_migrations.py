"""Migration smoke tests for the CRM service."""
from __future__ import annotations

from pathlib import Path
import sys

import pytest

SERVICE_DIR = Path(__file__).resolve().parents[1]
if str(SERVICE_DIR) in sys.path:
    sys.path.remove(str(SERVICE_DIR))
    sys.path.append(str(SERVICE_DIR))

try:  # pragma: no cover - skip if Alembic not installed in test environment
    from alembic import command  # type: ignore[attr-defined]
    from alembic.config import Config  # type: ignore[attr-defined]
except (ImportError, AttributeError):  # pragma: no cover - skip when dependency missing
    pytest.skip("alembic not available", allow_module_level=True)
from sqlalchemy import create_engine, inspect


def _config(tmp_path: Path) -> Config:
    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    db_path = tmp_path / "crm_migrations.db"
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return cfg


def test_upgrade_and_single_step_downgrade(tmp_path: Path) -> None:
    cfg = _config(tmp_path)
    command.upgrade(cfg, "head")

    engine = create_engine(cfg.get_main_option("sqlalchemy.url"))
    inspector = inspect(engine)
    assert "users" in inspector.get_table_names()

    command.downgrade(cfg, "-1")
    inspector = inspect(engine)
    assert "users" not in inspector.get_table_names()
    engine.dispose()
