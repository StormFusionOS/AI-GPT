"""Authentication flow tests."""
from __future__ import annotations

from app.api.routes.auth import login
from app.schemas.auth import LoginRequest


def test_login_success(override_settings) -> None:
    result = login(LoginRequest(email="sales@example.com", password="password123"))
    assert result.access_token
    assert result.token_type == "bearer"


def test_protected_requires_token(override_settings) -> None:
    from app.api.routes.leads import list_contacts
    import pytest

    with pytest.raises(Exception):
        list_contacts(authorization="invalid")
