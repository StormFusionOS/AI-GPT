"""Ops auth tests."""
from __future__ import annotations

from app.api.routes import auth


def test_login_success(override_settings) -> None:
    response = auth.login(email="ops@example.com", password="password123")
    assert "access_token" in response


def test_status_requires_role(override_settings) -> None:
    from app.api.routes.status import get_status
    import pytest

    with pytest.raises(Exception):
        get_status(authorization="invalid")
