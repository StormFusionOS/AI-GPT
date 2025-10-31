"""Ops status endpoint tests."""
from __future__ import annotations

from datetime import timedelta

from app.api.routes import auth, status
from app.core.config import get_settings
from app.security import create_token


def _token() -> str:
    settings = get_settings()
    return create_token({"sub": "ops@example.com", "role": "SEO_ENGINEER"}, expires_delta=timedelta(minutes=5))


def test_status_returns_checks(override_settings) -> None:
    token = _token()
    result = status.get_status(authorization=f"Bearer {token}")
    assert any(check["name"] == "database" for check in result["checks"])
