"""Authentication flow tests."""
from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException

from app.api.deps import require_sales_claims
from app.api.routes.auth import login
from app.schemas.auth import LoginRequest


def test_login_success(override_settings) -> None:
    result = login(LoginRequest(email="sales@example.com", password="password123"))
    assert result.access_token
    assert result.token_type == "bearer"


def test_protected_requires_token(override_settings) -> None:
    with pytest.raises(HTTPException) as exc:
        asyncio.run(require_sales_claims({"role": "SEO_ENGINEER"}))
    assert exc.value.status_code == 403

