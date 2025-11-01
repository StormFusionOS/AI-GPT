"""Ops auth tests."""
from __future__ import annotations

from datetime import timedelta

import pytest

from app.api.routes import auth, status
from app.security import create_token


def test_login_success(override_settings) -> None:
    response = auth.login(email="ops@example.com", password="password123")
    assert "access_token" in response


def test_status_requires_role(override_settings) -> None:
    with pytest.raises(Exception):
        status.get_status(authorization="invalid")


def test_status_allows_authorised_role(override_settings) -> None:
    token = create_token({"sub": "ops@example.com", "role": "SEO_ENGINEER"}, expires_delta=timedelta(minutes=5))
    payload = status.get_status(authorization=f"Bearer {token}")
    assert "checks" in payload
